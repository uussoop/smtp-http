# smtp-sanic

Minimal SMTP sender API using Sanic. Provides an authenticated `/send` endpoint that accepts SMTP credentials via environment variables.

## Environment Variables

- AUTH_KEY: Shared secret to authorize API calls
- SMTP_HOST: SMTP server hostname
- SMTP_PORT: SMTP server port (default 587)
- SMTP_USERNAME: SMTP username (optional if unauthenticated server)
- SMTP_PASSWORD: SMTP password (optional if unauthenticated server)
- SMTP_USE_TLS: Use STARTTLS (default true)
- SMTP_USE_SSL: Use implicit TLS/SSL (default false)
- SMTP_FROM_EMAIL: Default From email if not provided in request
- SMTP_FROM_NAME: Default From name if not provided in request

Note: Do not enable both STARTTLS and implicit SSL at the same time. If `SMTP_USE_SSL=true`, STARTTLS will be disabled.

## Run locally

```bash
pip install -r smtp-sanic/requirements.txt
python -m sanic smtp_sanic.app:app --host=0.0.0.0 --port=8000 --access-logs
```

## Request Format

POST `/send`

Headers:

- `X-Auth-Key: <AUTH_KEY>` or `Authorization: Bearer <AUTH_KEY>`

Body (JSON):

```json
{
  "to": "user@example.com",
  "subject": "Hello",
  "text": "Plain text body",
  "html": "<p>HTML body</p>",
  "from_email": "no-reply@example.com",
  "from_name": "Example App"
}
```

At least one of `text` or `html` is required.

## Docker

```bash
docker build -t ghcr.io/OWNER/smtp-sanic:latest -f smtp-sanic/Dockerfile .
docker run --rm -p 8000:8000 \
  -e AUTH_KEY=secret \
  -e SMTP_HOST=smtp.example.com \
  -e SMTP_PORT=587 \
  -e SMTP_USERNAME=username \
  -e SMTP_PASSWORD=password \
  -e SMTP_USE_TLS=true \
  ghcr.io/OWNER/smtp-sanic:latest
```

## GitHub Actions

Workflow builds and pushes to GHCR on pushes to main and tags.


