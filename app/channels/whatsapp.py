"""
Canal WhatsApp Business API (360dialog / Meta Cloud API).
"""
from fastapi import APIRouter, Request, HTTPException, Query
from loguru import logger
import httpx

from config.settings import settings
from app.agent.agent import process_message

router = APIRouter()


async def send_whatsapp_message(phone: str, text: str) -> None:
    """Envía un mensaje de texto vía WhatsApp Cloud API."""
    url = f"https://waba.360dialog.io/v1/messages"
    headers = {
        "D360-API-KEY": settings.whatsapp_api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": text}
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers, timeout=10)
        if resp.status_code not in (200, 201):
            logger.error(f"Error enviando mensaje WhatsApp: {resp.text}")


@router.get("/webhook/whatsapp")
async def whatsapp_verify(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default="")
):
    """Verificación del webhook requerida por Meta."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("WhatsApp webhook verificado correctamente")
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Recibe mensajes entrantes de WhatsApp."""
    body = await request.json()
    logger.debug(f"WhatsApp update: {body}")

    try:
        entry    = body["entry"][0]
        changes  = entry["changes"][0]
        value    = changes["value"]
        messages = value.get("messages", [])

        if not messages:
            return {"status": "ok"}

        msg   = messages[0]
        phone = msg["from"]
        mtype = msg.get("type", "")

        if mtype != "text":
            # Ignorar mensajes no texto (imagen, audio, etc.)
            await send_whatsapp_message(
                phone,
                "Solo puedo procesar mensajes de texto. Por favor escríbame su consulta."
            )
            return {"status": "ok"}

        text = msg["text"]["body"].strip()
        logger.info(f"WhatsApp [{phone}]: {text[:80]}")

        response = await process_message(
            session_id=f"wa_{phone}",
            user_message=text,
            channel="whatsapp"
        )

        await send_whatsapp_message(phone, response)

    except (KeyError, IndexError) as e:
        logger.warning(f"WhatsApp payload inesperado: {e}")

    return {"status": "ok"}
