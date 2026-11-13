"""Deployment configuration checks for Vercel, PrimeCloud, and Docker."""

import json
from pathlib import Path
import re

import pytest
from fastapi.testclient import TestClient

from app.main import _cors_origins, app


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_production_cors_requires_explicit_frontend_origins(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    with pytest.raises(RuntimeError, match="CORS_ORIGINS must list"):
        _cors_origins()

    monkeypatch.setenv("CORS_ORIGINS", "*")
    with pytest.raises(RuntimeError, match="cannot use"):
        _cors_origins()


def test_cors_origins_are_normalized_and_local_defaults_are_available(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "CORS_ORIGINS",
        " https://copilot.vercel.app/ , https://copilot.example.com ",
    )
    assert _cors_origins() == [
        "https://copilot.vercel.app",
        "https://copilot.example.com",
    ]

    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert _cors_origins() == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_vercel_build_and_spa_fallback_are_configured() -> None:
    config = json.loads((PROJECT_ROOT / "vercel.json").read_text())

    assert config["framework"] == "vite"
    assert config["buildCommand"] == "npm run build"
    assert config["outputDirectory"] == "dist"
    assert config["rewrites"] == [
        {"source": "/(.*)", "destination": "/index.html"}
    ]


def test_backend_procfile_uses_platform_assigned_port() -> None:
    procfile = (PROJECT_ROOT / "Procfile").read_text()

    assert "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}" in procfile


def test_cors_preflight_allows_attachment_removal() -> None:
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/media/example",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "DELETE",
                "Access-Control-Request-Headers": "authorization",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "DELETE" in response.headers["access-control-allow-methods"]


def test_nginx_logs_and_runtime_files_use_container_safe_paths() -> None:
    config = (PROJECT_ROOT / "deploy" / "nginx.conf").read_text()

    assert re.search(r"(?m)^\s*error_log\s+/dev/stderr(?:\s+\w+)?;", config)
    assert re.search(r"(?m)^\s*access_log\s+/dev/stdout\s*;", config)
    assert "/var/lib/nginx/logs" not in config
    assert re.search(r"(?m)^\s*pid\s+/tmp/nginx/nginx\.pid\s*;", config)
    temp_paths = {
        "client_body_temp_path": "client_body",
        "proxy_temp_path": "proxy",
        "fastcgi_temp_path": "fastcgi",
        "uwsgi_temp_path": "uwsgi",
        "scgi_temp_path": "scgi",
    }
    for directive, directory in temp_paths.items():
        assert re.search(
            rf"(?m)^\s*{directive}\s+/tmp/nginx/{directory}\s*;",
            config,
        )


def test_image_and_startup_preserve_non_root_proxy_and_readiness() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text()
    startup = (PROJECT_ROOT / "deploy" / "start.sh").read_text()
    nginx = (PROJECT_ROOT / "deploy" / "nginx.conf").read_text()

    assert "USER appuser" in dockerfile
    assert "chown -R appuser:appuser /app/data" in dockerfile
    assert "chmod 1777" in dockerfile
    assert "/tmp/nginx \\" in dockerfile
    for directory in ("client_body", "proxy", "fastcgi", "uwsgi", "scgi"):
        assert f"/tmp/nginx/{directory}" in dockerfile
    assert "USER appuser\n\nRUN nginx -t -e stderr -c /etc/nginx/nginx.conf" in dockerfile
    assert "COPY ai ./ai" in dockerfile
    assert "COPY data ./data" in dockerfile
    assert "python -m ai.ingestion.manifest" in dockerfile
    assert "python -m ai.ingestion.source_preview" in dockerfile
    assert "uvicorn app.main:app --host 127.0.0.1 --port 8000" in startup
    assert 'nginx -e stderr -c /etc/nginx/nginx.conf -g "daemon off;" &' in startup
    assert "http://127.0.0.1:8000/ready" in startup
    assert "location /ready" in nginx
    assert "proxy_pass http://127.0.0.1:8000/ready;" in nginx
    assert "http://127.0.0.1:8080/ready" in dockerfile
