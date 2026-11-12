FROM node:22-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM python:3.12-alpine

RUN apk add --no-cache nginx \
    && addgroup -S appuser \
    && adduser -S -D -H -G appuser appuser \
    && mkdir -p /app/data \
        /tmp/nginx/client_body \
        /tmp/nginx/proxy \
        /tmp/nginx/fastcgi \
        /tmp/nginx/uwsgi \
        /tmp/nginx/scgi \
    && chmod 1777 \
        /tmp/nginx/client_body \
        /tmp/nginx/proxy \
        /tmp/nginx/fastcgi \
        /tmp/nginx/uwsgi \
        /tmp/nginx/scgi \
    && chown -R appuser:appuser /app/data

WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY --from=build /app/dist /usr/share/nginx/html
COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY deploy/start.sh /usr/local/bin/start.sh

ENV PORT=8080 \
    APP_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN chmod +x /usr/local/bin/start.sh

USER appuser

RUN nginx -t -e stderr -c /etc/nginx/nginx.conf

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/ready >/dev/null || exit 1

CMD ["/usr/local/bin/start.sh"]
