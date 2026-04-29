"""
Tool: consultar_disponibilidad y crear_cita
Integración con Google Calendar API v3.
"""
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from loguru import logger
from config.lawyers import get_lawyer

TIMEZONE = "America/Bogota"

def _get_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from config.settings import settings

    creds = service_account.Credentials.from_service_account_file(
        settings.google_credentials_path,
        scopes=["https://www.googleapis.com/auth/calendar"]
    )
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def consultar_disponibilidad(area_legal: str, urgencia: str, duracion_minutos: int) -> dict:
    """Retorna hasta 3 slots libres según urgencia."""
    lawyer = get_lawyer(area_legal)
    if not lawyer:
        return {"error": f"No se encontró abogado para área: {area_legal}"}

    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)

    # Rango de búsqueda según urgencia
    days_map = {"alta": 2, "media": 3, "baja": 5}
    days_ahead = days_map.get(urgencia, 5)

    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()

    try:
        service = _get_service()

        # Consultar eventos existentes en el calendario del abogado
        events_result = service.events().list(
            calendarId=lawyer["calendar_id"],
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        busy_events = events_result.get("items", [])

        # Construir lista de horarios ocupados
        busy_slots = []
        for event in busy_events:
            start = event.get("start", {}).get("dateTime")
            end   = event.get("end", {}).get("dateTime")
            if start and end:
                busy_slots.append((
                    datetime.fromisoformat(start),
                    datetime.fromisoformat(end)
                ))

        # Generar slots candidatos (lunes-viernes, 8am-6pm)
        slots = []
        candidate = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        deadline = now + timedelta(days=days_ahead)

        while candidate < deadline and len(slots) < 3:
            # Solo días hábiles
            if candidate.weekday() >= 5:
                candidate += timedelta(hours=1)
                continue
            # Solo horario laboral
            if not (8 <= candidate.hour < 17):
                candidate += timedelta(hours=1)
                continue

            slot_end = candidate + timedelta(minutes=duracion_minutos)

            # Verificar que no choque con eventos existentes
            conflict = any(
                not (slot_end <= busy_start or candidate >= busy_end)
                for busy_start, busy_end in busy_slots
            )

            if not conflict:
                slots.append({
                    "inicio": candidate.strftime("%Y-%m-%dT%H:%M:%S"),
                    "fin": slot_end.strftime("%Y-%m-%dT%H:%M:%S"),
                    "label": candidate.strftime("%A %d de %B a las %I:%M %p")
                                      .replace("Monday","Lunes").replace("Tuesday","Martes")
                                      .replace("Wednesday","Miércoles").replace("Thursday","Jueves")
                                      .replace("Friday","Viernes")
                })
            candidate += timedelta(hours=1)

        return {
            "abogado": lawyer["name"],
            "area": lawyer["area"],
            "slots_disponibles": slots,
            "total": len(slots)
        }

    except Exception as e:
        logger.error(f"Error consultando calendario: {e}")
        return {"error": str(e), "slots_disponibles": []}


def crear_cita(
    area_legal: str,
    fecha_inicio: str,
    duracion_minutos: int,
    cliente_nombre: str,
    cliente_telefono: str,
    resumen_caso: str,
    urgencia: str
) -> dict:
    """Crea el evento en Google Calendar y retorna el link."""
    lawyer = get_lawyer(area_legal)
    if not lawyer:
        return {"error": f"No se encontró abogado para área: {area_legal}"}

    tz = ZoneInfo(TIMEZONE)
    try:
        dt_inicio = datetime.fromisoformat(fecha_inicio).replace(tzinfo=tz)
        dt_fin    = dt_inicio + timedelta(minutes=duracion_minutos)

        urgencia_label = {"alta": "🔴 URGENTE", "media": "🟡 Media", "baja": "🟢 Normal"}

        event = {
            "summary": f"[{urgencia_label.get(urgencia,'Normal')}] Consulta — {cliente_nombre}",
            "description": (
                f"Cliente: {cliente_nombre}\n"
                f"Teléfono: {cliente_telefono}\n"
                f"Área: {lawyer['area']}\n"
                f"Urgencia: {urgencia}\n\n"
                f"Resumen del caso:\n{resumen_caso}"
            ),
            "start": {"dateTime": dt_inicio.isoformat(), "timeZone": TIMEZONE},
            "end":   {"dateTime": dt_fin.isoformat(),    "timeZone": TIMEZONE},
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email",  "minutes": 60},
                    {"method": "popup",  "minutes": 15}
                ]
            }
        }

        service = _get_service()
        created = service.events().insert(
            calendarId=lawyer["calendar_id"],
            body=event,
            sendUpdates="all"
        ).execute()

        return {
            "success": True,
            "event_id": created.get("id"),
            "event_link": created.get("htmlLink"),
            "abogado": lawyer["name"],
            "fecha_inicio": dt_inicio.strftime("%A %d de %B de %Y a las %I:%M %p")
        }

    except Exception as e:
        logger.error(f"Error creando cita: {e}")
        return {"success": False, "error": str(e)}
