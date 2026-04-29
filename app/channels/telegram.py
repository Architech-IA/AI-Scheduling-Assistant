"""
Canal Telegram — recibe mensajes vía webhook y responde.
"""
from fastapi import APIRouter, Request, HTTPException
from loguru import logger
import httpx

from config.settings import settings
from app.agent.agent import process_message

router = APIRouter()


async def send_telegram_message(chat_id: str, text: str) -> None:
    """Envía un mensaje de texto al chat de Telegram."""
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            logger.error(f"Error enviando mensaje Telegram: {resp.text}")


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Endpoint que recibe los updates de Telegram."""
    # Verificar token secreto en el header (configurado al registrar el webhook)
    token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if token != settings.webhook_secret:
        raise HTTPException(status_code=403, detail="Unauthorized")

    update = await request.json()
    logger.debug(f"Telegram update: {update}")

    # Solo procesar mensajes de texto
    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id  = str(message["chat"]["id"])
    text     = message.get("text", "").strip()
    username = message.get("from", {}).get("username", "")

    if not text:
        return {"ok": True}

    # Ignorar comandos del sistema (excepto /start)
    if text.startswith("/") and text != "/start":
        return {"ok": True}

    if text == "/start":
        text = "Hola, quisiera información sobre sus servicios legales."

    logger.info(f"Telegram [{chat_id}] @{username}: {text[:80]}")

    # Procesar con el agente
    response = await process_message(
        session_id=f"tg_{chat_id}",
        user_message=text,
        channel="telegram"
    )

    # Responder al cliente
    await send_telegram_message(chat_id, response)
    return {"ok": True}
