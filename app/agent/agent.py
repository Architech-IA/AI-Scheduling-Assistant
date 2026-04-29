"""
Núcleo del agente.
Recibe un mensaje, consulta Claude con el historial y las tools,
ejecuta las tool calls que Claude solicite y retorna la respuesta final.
"""
import json
from loguru import logger
import anthropic

from config.settings import settings
from app.agent.prompt import build_system_prompt
from app.agent.session import append_message, get_history, save_metadata
from app.tools.registry import TOOLS
from app.tools import calendar, sheets, notify

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


# ── Dispatcher de tools ───────────────────────────────────────────
async def _execute_tool(tool_name: str, tool_input: dict, session_id: str, channel: str) -> str:
    """Ejecuta la tool solicitada por Claude y retorna el resultado como string."""
    logger.info(f"Tool call: {tool_name} | input: {tool_input}")

    if tool_name == "consultar_disponibilidad":
        result = calendar.consultar_disponibilidad(
            area_legal=tool_input["area_legal"],
            urgencia=tool_input["urgencia"],
            duracion_minutos=tool_input["duracion_minutos"]
        )
        # Guardar metadatos del caso en la sesión
        save_metadata(session_id, {
            "area_legal": tool_input["area_legal"],
            "urgencia": tool_input["urgencia"],
            "duracion": tool_input["duracion_minutos"]
        })

    elif tool_name == "crear_cita":
        result = calendar.crear_cita(
            area_legal=tool_input["area_legal"],
            fecha_inicio=tool_input["fecha_inicio"],
            duracion_minutos=tool_input["duracion_minutos"],
            cliente_nombre=tool_input["cliente_nombre"],
            cliente_telefono=tool_input["cliente_telefono"],
            resumen_caso=tool_input["resumen_caso"],
            urgencia=tool_input["urgencia"]
        )
        if result.get("success"):
            save_metadata(session_id, {
                "cita_creada": True,
                "event_id": result.get("event_id"),
                "cliente_nombre": tool_input["cliente_nombre"],
                "fecha_cita": tool_input["fecha_inicio"],
                "abogado": result.get("abogado")
            })

    elif tool_name == "guardar_registro":
        result = await _guardar_registro_async(tool_input, channel)

    elif tool_name == "notificar_abogado":
        result = await notify.notificar_abogado(
            area_legal=tool_input["area_legal"],
            cliente_nombre=tool_input["cliente_nombre"],
            cliente_telefono=tool_input["cliente_telefono"],
            fecha_cita=tool_input["fecha_cita"],
            resumen_caso=tool_input["resumen_caso"],
            urgencia=tool_input["urgencia"]
        )

    elif tool_name == "escalar_a_humano":
        result = await notify.escalar_a_humano(
            motivo=tool_input["motivo"],
            resumen_conversacion=tool_input["resumen_conversacion"],
            cliente_chat_id=session_id
        )

    else:
        result = {"error": f"Tool desconocida: {tool_name}"}

    return json.dumps(result, ensure_ascii=False)


async def _guardar_registro_async(tool_input: dict, channel: str) -> dict:
    return sheets.guardar_registro(
        cliente_nombre=tool_input["cliente_nombre"],
        cliente_telefono=tool_input["cliente_telefono"],
        area_legal=tool_input["area_legal"],
        urgencia=tool_input["urgencia"],
        abogado_nombre=tool_input["abogado_nombre"],
        fecha_cita=tool_input["fecha_cita"],
        resumen_caso=tool_input["resumen_caso"],
        canal=channel,
        complejidad=tool_input.get("complejidad", "simple"),
        tipo_cliente=tool_input.get("tipo_cliente", "persona_natural"),
    )


# ── Selección de modelo según turno ──────────────────────────────
def _select_model(history: list[dict]) -> str:
    """
    Modelo híbrido para optimizar costos:
    - Haiku para los primeros turnos de triage y clasificación
    - Sonnet para el turno final de confirmación (cuando ya hay cita creada)
    """
    # Si hay tool call de crear_cita en el historial, usar Sonnet para la confirmación
    for msg in history[-4:]:
        content = msg.get("content", "")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    if block.get("name") == "crear_cita":
                        return settings.model_confirm
    return settings.model_triage


# ── Función principal del agente ─────────────────────────────────
async def process_message(
    session_id: str,
    user_message: str,
    channel: str = "telegram"
) -> str:
    """
    Procesa un mensaje del cliente y retorna la respuesta del agente.

    Args:
        session_id: ID único de la conversación (chat_id en Telegram/WhatsApp)
        user_message: Texto del mensaje del cliente
        channel: "telegram" o "whatsapp"

    Returns:
        Texto de respuesta para enviar al cliente
    """
    # 1. Agregar mensaje del usuario al historial
    history = append_message(session_id, "user", user_message)
    model = _select_model(history)

    logger.info(f"[{session_id}] Procesando mensaje | modelo: {model} | turno: {len(history)//2}")

    messages = history.copy()

    # 2. Bucle de tool use — Claude puede encadenar múltiples tool calls
    max_iterations = 5
    for iteration in range(max_iterations):
        response = client.messages.create(
            model=model,
            max_tokens=settings.max_tokens,
            system=build_system_prompt(),
            tools=TOOLS,
            messages=messages
        )

        logger.debug(f"[{session_id}] stop_reason: {response.stop_reason}")

        # Si Claude terminó de responder (sin tool calls pendientes)
        if response.stop_reason == "end_turn":
            # Extraer texto de la respuesta
            text_blocks = [
                block.text for block in response.content
                if hasattr(block, "text")
            ]
            final_response = "\n".join(text_blocks).strip()

            # Guardar respuesta del asistente en el historial
            append_message(session_id, "assistant", final_response)
            return final_response

        # Si Claude quiere llamar tools
        elif response.stop_reason == "tool_use":
            # Agregar la respuesta de Claude (con tool calls) al contexto
            messages.append({"role": "assistant", "content": response.content})

            # Ejecutar cada tool call y recolectar resultados
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_result = await _execute_tool(
                        tool_name=block.name,
                        tool_input=block.input,
                        session_id=session_id,
                        channel=channel
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result
                    })

            # Agregar resultados de las tools al contexto
            messages.append({"role": "user", "content": tool_results})

        else:
            # stop_reason inesperado
            logger.warning(f"[{session_id}] stop_reason inesperado: {response.stop_reason}")
            break

    # Si llegamos aquí, algo salió mal en el bucle
    fallback = (
        "Lo siento, en este momento no puedo procesar su solicitud. "
        "Por favor comuníquese directamente con nuestra oficina."
    )
    append_message(session_id, "assistant", fallback)
    return fallback
