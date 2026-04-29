"""
Tool: notificar_abogado y escalar_a_humano
Envía mensajes por Telegram al abogado asignado o a la secretaria.
"""
from loguru import logger
from config.lawyers import get_lawyer

# Chat ID de la secretaria / CEO para escalamientos
ESCALATION_CHAT_ID = ""  # Completar con el chat ID real


async def notificar_abogado(
    area_legal: str,
    cliente_nombre: str,
    cliente_telefono: str,
    fecha_cita: str,
    resumen_caso: str,
    urgencia: str
) -> dict:
    """Envía mensaje al abogado con los datos de la nueva cita."""
    from telegram import Bot
    from config.settings import settings

    lawyer = get_lawyer(area_legal)
    if not lawyer or not lawyer.get("telegram_chat_id"):
        logger.warning(f"No hay chat_id de Telegram para abogado de área: {area_legal}")
        return {"success": False, "error": "Chat ID del abogado no configurado."}

    urgencia_emoji = {"alta": "🔴", "media": "🟡", "baja": "🟢"}.get(urgencia, "⚪")

    message = (
        f"{urgencia_emoji} *Nueva cita agendada*\n\n"
        f"*Cliente:* {cliente_nombre}\n"
        f"*Teléfono:* {cliente_telefono}\n"
        f"*Fecha:* {fecha_cita}\n"
        f"*Urgencia:* {urgencia.upper()}\n\n"
        f"*Resumen del caso:*\n{resumen_caso}"
    )

    try:
        bot = Bot(token=settings.telegram_bot_token)
        await bot.send_message(
            chat_id=lawyer["telegram_chat_id"],
            text=message,
            parse_mode="Markdown"
        )
        logger.info(f"Notificación enviada al abogado de {area_legal}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error notificando abogado: {e}")
        return {"success": False, "error": str(e)}


async def escalar_a_humano(
    motivo: str,
    resumen_conversacion: str,
    cliente_chat_id: str = ""
) -> dict:
    """Notifica a la secretaria / CEO para atención manual."""
    from telegram import Bot
    from config.settings import settings

    if not ESCALATION_CHAT_ID:
        logger.warning("ESCALATION_CHAT_ID no configurado")
        return {"success": False, "error": "Chat ID de escalamiento no configurado."}

    motivos = {
        "cliente_solicita_humano":       "El cliente solicitó hablar con una persona.",
        "no_clasificable":               "No fue posible clasificar el caso automáticamente.",
        "sin_disponibilidad_urgente":    "No hay disponibilidad para un caso urgente.",
        "multiples_intentos_fallidos":   "Múltiples intentos de clasificación fallidos.",
    }

    message = (
        f"⚠️ *Escalamiento requerido*\n\n"
        f"*Motivo:* {motivos.get(motivo, motivo)}\n\n"
        f"*Resumen de la conversación:*\n{resumen_conversacion}\n\n"
        f"Por favor atienda este cliente manualmente."
    )

    try:
        bot = Bot(token=settings.telegram_bot_token)
        await bot.send_message(
            chat_id=ESCALATION_CHAT_ID,
            text=message,
            parse_mode="Markdown"
        )
        return {"success": True, "message": "Escalamiento notificado correctamente."}
    except Exception as e:
        logger.error(f"Error en escalamiento: {e}")
        return {"success": False, "error": str(e)}
