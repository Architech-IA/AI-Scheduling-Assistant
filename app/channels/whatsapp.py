"""
Canal WhatsApp — YCloud API (Meta BSP oficial).
"""
from fastapi import APIRouter, Request, HTTPException, Query
from loguru import logger
import httpx

from config.settings import settings
from app.agent.agent import process_message

router = APIRouter()

YCLOUD_API_URL = "https://api.ycloud.com/v2/whatsapp/messages/sendDirectly"


async def send_whatsapp_message(phone: str, text: str) -> None:
    """Envía un mensaje de texto vía YCloud API."""
    headers = {
        "X-API-Key": settings.ycloud_api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "from": settings.ycloud_phone_number,
        "to": phone,
        "type": "text",
        "text": {"body": text}
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(YCLOUD_API_URL, json=payload, headers=headers, timeout=15)
        if resp.status_code not in (200, 201):
            logger.error(f"Error enviando WhatsApp: {resp.status_code} {resp.text}")


@router.get("/webhook/whatsapp")
async def whatsapp_verify(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default="")
):
    """Verificación del webhook (Meta Cloud API / YCloud)."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("WhatsApp webhook verificado")
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Recibe mensajes entrantes de WhatsApp vía YCloud webhook."""
    body = await request.json()
    logger.debug(f"WhatsApp webhook: {body}")

    try:
        # YCloud envía payload similar a Meta Cloud API
        entry    = body.get("entry", [{}])[0]
        changes  = entry.get("changes", [{}])[0]
        value    = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "ok"}

        msg   = messages[0]
        phone = msg.get("from", "")
        mtype = msg.get("type", "")

        if mtype != "text":
            await send_whatsapp_message(
                phone,
                "Solo puedo procesar mensajes de texto."
            )
            return {"status": "ok"}

        text = msg.get("text", {}).get("body", "").strip()
        if not text:
            return {"status": "ok"}

        logger.info(f"WhatsApp [{phone}]: {text[:80]}")

        response = await process_message(
            session_id=f"wa_{phone}",
            user_message=text,
            channel="whatsapp"
        )

        await send_whatsapp_message(phone, response)

    except (KeyError, IndexError, AttributeError) as e:
        logger.warning(f"WhatsApp payload inesperado: {e}")

    return {"status": "ok"}
