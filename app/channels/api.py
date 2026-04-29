"""
Canal API REST — endpoint JSON para n8n y consumidores externos.
Recibe solicitudes estructuradas y retorna respuestas JSON limpia.
"""
from uuid import uuid4
from fastapi import APIRouter
from pydantic import BaseModel, Field
from loguru import logger

from app.agent.agent import process_message

router = APIRouter()


class ProcessRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Mensaje del usuario")
    session_id: str = Field("", description="ID de sesión. Si se omite, se genera uno nuevo.")
    channel: str = Field("api", pattern="^(api|telegram|whatsapp)$")


class ProcessResponse(BaseModel):
    success: bool
    response: str
    session_id: str
    channel: str


@router.post("/api/process", response_model=ProcessResponse)
async def api_process(body: ProcessRequest):
    """Endpoint principal para n8n. Procesa un mensaje y retorna la respuesta del agente."""
    session_id = body.session_id or f"api_{uuid4().hex[:12]}"
    logger.info(f"API [{session_id}]: {body.message[:80]}")

    try:
        response = await process_message(
            session_id=session_id,
            user_message=body.message,
            channel=body.channel,
        )
        return ProcessResponse(
            success=True,
            response=response,
            session_id=session_id,
            channel=body.channel,
        )
    except Exception as e:
        logger.error(f"API error [{session_id}]: {e}")
        return ProcessResponse(
            success=False,
            response="Error interno del servidor. Intente nuevamente.",
            session_id=session_id,
            channel=body.channel,
        )
