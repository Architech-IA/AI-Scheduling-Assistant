"""
Tool: guardar_registro
Integración con Google Sheets API.
"""
from datetime import datetime
from loguru import logger


def _get_client():
    import gspread
    from google.oauth2 import service_account
    from config.settings import settings

    creds = service_account.Credentials.from_service_account_file(
        settings.google_credentials_path,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    return gspread.authorize(creds)


def guardar_registro(
    cliente_nombre: str,
    cliente_telefono: str,
    area_legal: str,
    urgencia: str,
    abogado_nombre: str,
    fecha_cita: str,
    resumen_caso: str,
    canal: str,
    complejidad: str = "simple",
    tipo_cliente: str = "persona_natural",
) -> dict:
    """Escribe una fila en Google Sheets con los datos del caso."""
    from config.settings import settings

    try:
        client = _get_client()
        sheet = client.open_by_key(settings.google_sheets_id)

        # Usar primera hoja o crearla si no existe
        try:
            ws = sheet.worksheet("Registro de Casos")
        except gspread.WorksheetNotFound:
            ws = sheet.add_worksheet("Registro de Casos", rows=1000, cols=12)
            # Encabezados
            ws.append_row([
                "Fecha Registro", "Cliente", "Teléfono", "Área Legal",
                "Urgencia", "Complejidad", "Tipo Cliente", "Abogado",
                "Fecha Cita", "Canal", "Resumen", "Estado"
            ])

        row = [
            datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            cliente_nombre,
            cliente_telefono,
            area_legal,
            urgencia,
            complejidad,
            tipo_cliente,
            abogado_nombre,
            fecha_cita,
            canal,
            resumen_caso,
            "Agendada"
        ]

        ws.append_row(row)
        logger.info(f"Registro guardado: {cliente_nombre} — {area_legal} — {fecha_cita}")

        return {"success": True, "message": "Registro guardado correctamente en Google Sheets."}

    except Exception as e:
        logger.error(f"Error guardando registro en Sheets: {e}")
        return {"success": False, "error": str(e)}
