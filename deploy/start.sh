#!/bin/sh
set -eu

uvicorn app.main:app --host 127.0.0.1 --port 8000 &
backend_pid=$!
nginx_pid=

cleanup() {
  if [ -n "$nginx_pid" ]; then
    kill "$nginx_pid" 2>/dev/null || true
    wait "$nginx_pid" 2>/dev/null || true
  fi
  kill "$backend_pid" 2>/dev/null || true
  wait "$backend_pid" 2>/dev/null || true
}

trap cleanup INT TERM EXIT

attempt=0
while [ "$attempt" -lt 30 ]; do
  if ! kill -0 "$backend_pid" 2>/dev/null; then
    wait "$backend_pid" || true
    echo "Backend exited before becoming ready" >&2
    exit 1
  fi
  if wget -qO- http://127.0.0.1:8000/ready >/dev/null 2>&1; then
    break
  fi
  attempt=$((attempt + 1))
  sleep 2
done

if [ "$attempt" -ge 30 ]; then
  echo "Backend did not become ready within 60 seconds" >&2
  exit 1
fi

nginx -c /etc/nginx/nginx.conf -g "daemon off;" &
nginx_pid=$!

while kill -0 "$backend_pid" 2>/dev/null && kill -0 "$nginx_pid" 2>/dev/null; do
  sleep 2
done

if ! kill -0 "$backend_pid" 2>/dev/null; then
  wait "$backend_pid" || true
  echo "Backend exited unexpectedly" >&2
  exit 1
fi

wait "$nginx_pid"
