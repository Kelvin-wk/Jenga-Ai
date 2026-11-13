"""Deterministic, role-aware chat orchestration."""

from __future__ import annotations

import re
from typing import Literal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.ai import generate_grounded_answer
from app.services.media import ChatAttachment
from app.tools.catalog import lookup_products
from app.tools.safety import safety_notice

Confidence = Literal["high", "medium", "low"]
ChatResult = tuple[str, str, list[str], list[str], Confidence]


def _is_restricted_query(query: str) -> bool:
    return bool(
        re.search(
            r"\b(internal\s+margin|profit\s+margin|markup|cost\s+price|restricted\s+service\s+manual|service\s+manual)\b",
            query,
            flags=re.IGNORECASE,
        )
    )


def route_query(
    query: str,
    role: str,
    db: Session,
    attachments: list[ChatAttachment] | None = None,
) -> ChatResult:
    lowered = query.lower()
    attachments = attachments or []
    if _is_restricted_query(query) and role == "customer":
        return (
            "I cannot provide internal margins or restricted service manuals.",
            "access_control",
            [],
            ["This request is restricted to authorised Jenga engineers."],
            "high",
        )
    if attachments:
        products = lookup_products(db)
        answer = generate_grounded_answer(
            query,
            role,
            products,
            attachments=attachments,
        )
        if answer is None:
            raise HTTPException(
                status_code=503,
                detail="Attachment analysis requires OPENAI_API_KEY to be configured.",
            )
        return (
            answer,
            "openai_assistant",
            ["Product catalog", *(f"User attachment: {item.filename}" for item in attachments)],
            [
                "AI-generated answer; verify important specifications with an authorised consultant.",
                "Uploaded materials are user-provided and are not independently verified.",
            ],
            "medium",
        )
    if any(word in lowered for word in ("price", "cost", "quote", "pricing")):
        products = lookup_products(db)
        if not products:
            return "No product pricing data is currently available.", "price_lookup", [], ["Catalog data unavailable."], "low"
        lines = [f"{product.name} ({product.model_number}): KSh {product.price_ksh:,}" for product in products]
        return (
            "Available catalog pricing: " + "; ".join(lines),
            "price_lookup",
            ["Product catalog"],
            ["Prices are indicative and should be confirmed by an authorised consultant."],
            "high",
        )
    if role == "engineer" and any(word in lowered for word in ("fault", "troubleshoot", "safety", "alarm")):
        answer, citations, warnings, confidence = safety_notice()
        return answer, "safety_notice", citations, warnings, confidence
    products = lookup_products(db)
    answer = generate_grounded_answer(query, role, products)
    if answer is not None:
        return (
            answer,
            "openai_assistant",
            ["Product catalog"],
            ["AI-generated answer; verify important specifications with an authorised consultant."],
            "medium",
        )
    return (
        "I can answer grounded questions about Jenga products, specifications, and catalog pricing. "
        "Please include a product name or model number.",
        "product_catalog",
        ["Product catalog"],
        ["AI is not configured; this response is limited to verified catalog data."],
        "medium",
    )
