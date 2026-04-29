"""
Punto de entrada de la aplicación FastAPI.
"""
import sys
from loguru import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.requests import Request
from starlette.responses import JSONResponse

from config.settings import settings
from app.channels.telegram import router as telegram_router
from app.channels.whatsapp import router as whatsapp_router
from app.channels.api import router as api_router


# ── Logging ──────────────────────────────────────────────────────
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    level=settings.log_level
)
logger.add(
    "logs/agent.log",
    rotation="1 day",
    retention="90 days",
    level="DEBUG",
    serialize=True  # JSON estructurado para análisis posterior
)


# ── Startup / Shutdown ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Iniciando Asistente de Agendamiento con IA — {settings.firma_nombre}")
    logger.info(f"Entorno: {settings.environment}")
    logger.info(f"Modelo triage: {settings.model_triage}")
    logger.info(f"Modelo confirmación: {settings.model_confirm}")
    yield
    logger.info("Agente detenido.")


# ── App ───────────────────────────────────────────────────────────
app = FastAPI(
    title="Asistente de Agendamiento con IA",
    description="Agente conversacional de clasificación y agendamiento automático de citas",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# ── Manejadores de errores globales ────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Error interno del servidor."}
    )


# Registrar rutas de canales
app.include_router(telegram_router)
app.include_router(whatsapp_router)
app.include_router(api_router)


@app.get("/")
async def health():
    return {
        "status": "ok",
        "service": "Asistente de Agendamiento con IA",
        "firma": settings.firma_nombre,
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
