"""Deployment configuration checks for the combined Nginx/FastAPI image."""

from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_nginx_logs_and_runtime_files_use_container_safe_paths() -> None:
    config = (PROJECT_ROOT / "deploy" / "nginx.conf").read_text()

    assert re.search(r"(?m)^\s*error_log\s+/dev/stderr(?:\s+\w+)?;", config)
    assert re.search(r"(?m)^\s*access_log\s+/dev/stdout\s*;", config)
    assert "/var/lib/nginx/logs" not in config
    assert re.search(r"(?m)^\s*pid\s+/tmp/nginx\.pid\s*;", config)
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
