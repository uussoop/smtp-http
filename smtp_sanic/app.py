import os
from email.message import EmailMessage
from typing import Any, Dict, Optional

from sanic import Sanic, Request, json
from sanic.exceptions import Unauthorized, InvalidUsage
import aiosmtplib


def get_env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


app = Sanic("smtp-sanic")


def _auth_from_request(request: Request) -> Optional[str]:
    # Support either X-Auth-Key or Authorization: Bearer <key>
    header_key = request.headers.get("x-auth-key") or request.headers.get(
        "X-Auth-Key"
    )
    if header_key:
        return header_key
    auth_header = request.headers.get("authorization") or request.headers.get(
        "Authorization"
    )
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return None


@app.get("/health")
async def health(_request: Request):
    return json({"status": "ok"})


@app.post("/send")
async def send_email(request: Request):
    auth_key_required = get_required_env("AUTH_KEY")
    provided_key = _auth_from_request(request)
    if not provided_key or provided_key != auth_key_required:
        raise Unauthorized("Invalid or missing auth key")

    try:
        payload: Dict[str, Any] = request.json or {}
    except Exception as exc:  # noqa: BLE001
        raise InvalidUsage("Invalid JSON body") from exc

    to = payload.get("to")
    subject = payload.get("subject")
    text_body = payload.get("text")
    html_body = payload.get("html")
    from_email = payload.get("from_email")
    from_name = payload.get("from_name")

    if not to or not subject or (not text_body and not html_body):
        raise InvalidUsage(
            "Fields 'to', 'subject' and at least one of 'text' or 'html' are required"
        )

    smtp_host = get_required_env("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    use_tls = get_env_bool("SMTP_USE_TLS", True)
    use_ssl = get_env_bool("SMTP_USE_SSL", False)

    default_from_email = os.getenv("SMTP_FROM_EMAIL") or smtp_user or ""
    from_email = from_email or default_from_email
    default_from_name = os.getenv("SMTP_FROM_NAME", "")
    from_name = from_name or default_from_name

    if not from_email:
        raise InvalidUsage(
            "No 'from_email' provided and SMTP_FROM_EMAIL/SMTP_USERNAME not set"
        )

    message = EmailMessage()
    display_from = f"{from_name} <{from_email}>" if from_name else from_email
    message["From"] = display_from
    message["To"] = to if isinstance(to, str) else ", ".join(to)
    message["Subject"] = subject

    if text_body and html_body:
        message.set_content(text_body)
        message.add_alternative(html_body, subtype="html")
    elif html_body:
        message.add_alternative(html_body, subtype="html")
    else:
        message.set_content(text_body or "")

    try:
        # Prefer the convenience function which supports both implicit TLS and STARTTLS
        send_result = await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_pass,
            use_tls=use_ssl,
            start_tls=use_tls if not use_ssl else False,
            timeout=30,
        )
    except Exception as exc:  # noqa: BLE001
        return json({"status": "error", "error": str(exc)}, status=500)

    # Normalize response (supports aiosmtplib returning tuple(code, message) or an object with .code/.message)
    code = None
    response_message = None
    if isinstance(send_result, tuple):
        if len(send_result) >= 1:
            code = send_result[0]
        if len(send_result) >= 2:
            response_message = (
                send_result[1].decode() if isinstance(send_result[1], (bytes, bytearray)) else str(send_result[1])
            )
    else:
        code = getattr(send_result, "code", None)
        raw_message = getattr(send_result, "message", None)
        if raw_message is not None:
            response_message = raw_message.decode() if isinstance(raw_message, (bytes, bytearray)) else str(raw_message)

    message_id = message["Message-ID"] if "Message-ID" in message else None
    return json({"status": "sent", "code": code, "message": response_message, "messageId": message_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))


