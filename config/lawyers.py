"""
Matriz de abogados especialistas.
Completar con los datos reales de la firma antes del piloto.
"""

from typing import TypedDict

class Lawyer(TypedDict):
    name: str
    area: str
    calendar_id: str       # ID del calendario de Google del abogado
    telegram_chat_id: str  # Chat ID de Telegram del abogado para notificaciones
    available_hours: str   # Descripción de horario para el agente

LAWYERS: dict[str, Lawyer] = {
    "penal": {
        "name": "Dr. [Nombre Apellido]",
        "area": "Derecho Penal",
        "calendar_id": "abogado.penal@firma.com",
        "telegram_chat_id": "",
        "available_hours": "Lunes a viernes 8am-6pm, sábados 9am-12pm",
    },
    "civil": {
        "name": "Dra. [Nombre Apellido]",
        "area": "Derecho Civil",
        "calendar_id": "abogado.civil@firma.com",
        "telegram_chat_id": "",
        "available_hours": "Lunes a viernes 8am-5pm",
    },
    "laboral": {
        "name": "Dr. [Nombre Apellido]",
        "area": "Derecho Laboral",
        "calendar_id": "abogado.laboral@firma.com",
        "telegram_chat_id": "",
        "available_hours": "Lunes a viernes 9am-6pm",
    },
    "mercantil": {
        "name": "Dra. [Nombre Apellido]",
        "area": "Derecho Mercantil / Corporativo",
        "calendar_id": "abogado.mercantil@firma.com",
        "telegram_chat_id": "",
        "available_hours": "Lunes a viernes 8am-6pm",
    },
    "familiar": {
        "name": "Dra. [Nombre Apellido]",
        "area": "Derecho de Familia",
        "calendar_id": "abogado.familiar@firma.com",
        "telegram_chat_id": "",
        "available_hours": "Lunes a viernes 9am-5pm",
    },
    "administrativo": {
        "name": "Dr. [Nombre Apellido]",
        "area": "Derecho Administrativo",
        "calendar_id": "abogado.admin@firma.com",
        "telegram_chat_id": "",
        "available_hours": "Lunes a viernes 8am-5pm",
    },
}

AREAS = list(LAWYERS.keys())

def get_lawyer(area: str) -> Lawyer | None:
    return LAWYERS.get(area.lower())

def get_lawyers_summary() -> str:
    """Resumen para incluir en el prompt del sistema."""
    lines = []
    for area, lawyer in LAWYERS.items():
        lines.append(f"- {area.upper()}: {lawyer['name']} ({lawyer['available_hours']})")
    return "\n".join(lines)
