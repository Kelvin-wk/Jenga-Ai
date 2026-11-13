"""Deterministic, role-aware chat orchestration."""

from __future__ import annotations

import re
from typing import Literal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.database import ProductDB
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


def _domain_knowledge_answer(
    query: str, products: list[ProductDB]
) -> tuple[str, list[str]]:
    lowered = query.lower()
    category_terms = {
        "generator": ("generator", "genset", "jcg"),
        "transformer": ("transformer", "jct"),
        "solar": ("solar", "inverter", "jcs", "photovoltaic", "pv"),
    }
    relevant = [
        product
        for product in products
        if product.model_number.lower() in lowered
        or product.name.lower() in lowered
        or any(
            term in lowered
            for term in category_terms.get(product.category.lower(), ())
        )
    ]
    if not relevant and any(
        term in lowered
        for term in ("equipment", "product", "catalog", "catalogue", "available")
    ):
        catalogue = "; ".join(
            f"{product.name} ({product.model_number}: {product.specifications})"
            for product in products
        )
        if catalogue:
            return (
                f"The current Jenga catalogue includes: {catalogue}. Tell me a model "
                "or the electrical/load requirement you want to understand.",
                ["Product catalog"],
            )
        return (
            "No product records are currently available in the Jenga catalogue. "
            "Share the equipment type and nameplate details and I can explain what "
            "to check.",
            ["Product catalog"],
        )

    if relevant:
        product = relevant[0]
        category = product.category.lower()
        if category == "generator":
            explanation = (
                "A generator converts mechanical energy into electrical power. "
                "Its kVA rating is apparent power; usable kW depends on the rated "
                "power factor and operating conditions."
            )
        elif category == "transformer":
            explanation = (
                "A transformer transfers AC electrical energy between circuits "
                "and can step voltage up or down. It does not change the supply "
                "frequency."
            )
        elif category == "solar":
            explanation = (
                "A solar inverter converts DC power from photovoltaic equipment "
                "to AC power for compatible loads. PV voltage range, phase, "
                "battery compatibility, and grid requirements must be checked "
                "against the manufacturer documentation."
            )
        else:
            explanation = (
                "Equipment selection depends on the load, site supply, duty cycle, "
                "and the manufacturer's installation requirements."
            )
        answer = (
            f"{product.name} ({product.model_number}) is listed in the Jenga "
            f"catalogue as {product.category}. Recorded specifications: "
            f"{product.specifications}. {explanation} Confirm suitability with "
            "the equipment nameplate and an authorised engineer."
        )
        sources = ["Product catalog", f"{product.name} ({product.model_number})"]
        return answer, sources

    if "power factor" in lowered or "kva" in lowered and "kw" in lowered:
        return (
            "In an AC system, power factor is the ratio of real power (kW) to "
            "apparent power (kVA). It affects how much usable real power a given "
            "kVA-rated supply can deliver. Use the equipment nameplate and the "
            "actual load power factor when sizing equipment.",
            ["General electrical domain knowledge"],
        )

    catalogue = "; ".join(
        f"{product.name} ({product.model_number}: {product.specifications})"
        for product in products
    )
    if catalogue:
        return (
            "I can help with generator, transformer, and solar inverter basics. "
            f"The current Jenga catalogue includes: {catalogue}. Tell me a model "
            "or the electrical/load requirement you want to understand.",
            ["Product catalog"],
        )
    return (
        "I can help with general industrial equipment questions, but no product "
        "catalogue records are currently available. Please share the equipment "
        "type and its nameplate details.",
        ["General equipment domain knowledge"],
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
    answer, citations = _domain_knowledge_answer(query, products)
    return (
        answer,
        "domain_knowledge",
        citations,
        [
            "This response uses built-in domain guidance and catalogue data; verify equipment selection and safety requirements with an authorised engineer."
        ],
        "medium",
    )
