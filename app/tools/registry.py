"""
Definición de las 4 tools que Claude puede invocar.
Este archivo es la única fuente de verdad para el function calling.
"""

TOOLS = [
    {
        "name": "consultar_disponibilidad",
        "description": (
            "Consulta los horarios disponibles de un abogado en Google Calendar. "
            "Úsala ANTES de ofrecer horarios al cliente. "
            "Retorna una lista de slots libres en los próximos días."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "area_legal": {
                    "type": "string",
                    "enum": ["penal", "civil", "laboral", "mercantil", "familiar", "administrativo"],
                    "description": "Área legal del caso, determina qué abogado se consulta."
                },
                "urgencia": {
                    "type": "string",
                    "enum": ["alta", "media", "baja"],
                    "description": "Nivel de urgencia: alta=hoy/mañana, media=3 días, baja=5 días."
                },
                "duracion_minutos": {
                    "type": "integer",
                    "enum": [30, 60],
                    "description": "Duración de la cita: 30 para consulta simple, 60 para caso complejo."
                }
            },
            "required": ["area_legal", "urgencia", "duracion_minutos"]
        }
    },
    {
        "name": "crear_cita",
        "description": (
            "Agenda la cita en Google Calendar una vez que el cliente confirmó el horario. "
            "Solo llamar cuando el cliente haya elegido explícitamente un slot."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "area_legal": {
                    "type": "string",
                    "enum": ["penal", "civil", "laboral", "mercantil", "familiar", "administrativo"]
                },
                "fecha_inicio": {
                    "type": "string",
                    "description": "Fecha y hora de inicio en formato ISO 8601. Ej: 2025-05-13T09:00:00"
                },
                "duracion_minutos": {
                    "type": "integer",
                    "enum": [30, 60]
                },
                "cliente_nombre": {
                    "type": "string",
                    "description": "Nombre completo del cliente."
                },
                "cliente_telefono": {
                    "type": "string",
                    "description": "Número de teléfono del cliente (con código de país)."
                },
                "resumen_caso": {
                    "type": "string",
                    "description": "Resumen breve del caso en 2-3 oraciones para que el abogado se prepare."
                },
                "urgencia": {
                    "type": "string",
                    "enum": ["alta", "media", "baja"]
                }
            },
            "required": [
                "area_legal", "fecha_inicio", "duracion_minutos",
                "cliente_nombre", "cliente_telefono", "resumen_caso", "urgencia"
            ]
        }
    },
    {
        "name": "guardar_registro",
        "description": (
            "Guarda el registro del caso en Google Sheets. "
            "Llamar justo después de crear_cita para dejar trazabilidad."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cliente_nombre":    {"type": "string"},
                "cliente_telefono":  {"type": "string"},
                "area_legal":        {"type": "string"},
                "urgencia":          {"type": "string"},
                "complejidad":       {"type": "string", "enum": ["simple", "complejo"]},
                "tipo_cliente":      {"type": "string", "enum": ["persona_natural", "empresa"]},
                "abogado_nombre":    {"type": "string"},
                "fecha_cita":        {"type": "string"},
                "resumen_caso":      {"type": "string"},
                "canal":             {"type": "string", "enum": ["telegram", "whatsapp"]}
            },
            "required": [
                "cliente_nombre", "cliente_telefono", "area_legal",
                "urgencia", "abogado_nombre", "fecha_cita", "resumen_caso", "canal"
            ]
        }
    },
    {
        "name": "notificar_abogado",
        "description": (
            "Envía una notificación al abogado asignado con el resumen del caso y los datos de la cita. "
            "Llamar después de guardar_registro."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "area_legal":       {"type": "string"},
                "cliente_nombre":   {"type": "string"},
                "cliente_telefono": {"type": "string"},
                "fecha_cita":       {"type": "string"},
                "resumen_caso":     {"type": "string"},
                "urgencia":         {"type": "string"}
            },
            "required": [
                "area_legal", "cliente_nombre", "cliente_telefono",
                "fecha_cita", "resumen_caso", "urgencia"
            ]
        }
    },
    {
        "name": "escalar_a_humano",
        "description": (
            "Escala la conversación a una persona humana (secretaria o CEO). "
            "Usar cuando: el cliente lo pide, no se puede clasificar el caso, "
            "no hay disponibilidad urgente, o hay más de 3 intentos fallidos de clasificación."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "motivo": {
                    "type": "string",
                    "enum": [
                        "cliente_solicita_humano",
                        "no_clasificable",
                        "sin_disponibilidad_urgente",
                        "multiples_intentos_fallidos"
                    ]
                },
                "resumen_conversacion": {
                    "type": "string",
                    "description": "Resumen de lo conversado hasta el momento para contexto del humano."
                }
            },
            "required": ["motivo", "resumen_conversacion"]
        }
    }
]
