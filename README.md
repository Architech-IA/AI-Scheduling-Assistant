# Asistente de Agendamiento con IA

Agente conversacional de clasificación y agendamiento automático de citas.
Desarrollado para **Fase 1 — Piloto con Telegram**.

## Estructura del proyecto

```
scheduling-agent/
├── app/
│   ├── agent/
│   │   ├── agent.py      # Núcleo del agente — bucle de tool use
│   │   ├── prompt.py     # Prompt del sistema con criterios de clasificación
│   │   └── session.py    # Gestión de sesiones (Redis / SQLite fallback)
│   ├── tools/
│   │   ├── registry.py   # Definición de tools para Claude (function calling)
│   │   ├── calendar.py   # Tool: consultar_disponibilidad y crear_cita
│   │   ├── sheets.py     # Tool: guardar_registro en Google Sheets
│   │   └── notify.py     # Tool: notificar_abogado y escalar_a_humano
│   ├── channels/
│   │   ├── telegram.py   # Canal Telegram — webhook y respuesta
│   │   └── whatsapp.py   # Canal WhatsApp Business API
│   └── main.py           # FastAPI app — punto de entrada
├── config/
│   ├── settings.py       # Variables de entorno con Pydantic Settings
│   └── lawyers.py        # Matriz de abogados especialistas ← COMPLETAR
├── scripts/
│   └── setup.sh          # Setup completo del servidor
├── .env.example          # Variables de entorno requeridas ← COPIAR A .env
├── requirements.txt      # Dependencias Python
└── scheduling-agent.service  # Servicio systemd para VPS
```

## Inicio rápido

```bash
# 1. Clonar y configurar
git clone <repo> && cd scheduling-agent
cp .env.example .env
# Editar .env con tus credenciales

# 2. Completar matriz de abogados
# Editar config/lawyers.py

# 3. Instalar dependencias
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4. Correr en desarrollo
uvicorn app.main:app --reload --port 8000

# 5. Registrar webhook de Telegram
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<DOMINIO>/webhook/telegram&secret_token=<WEBHOOK_SECRET>"
```

## Credenciales requeridas

| Credencial | Dónde obtenerla |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `TELEGRAM_BOT_TOKEN` | @BotFather en Telegram |
| `GOOGLE_CREDENTIALS_PATH` | Google Cloud Console → Service Account |
| `GOOGLE_SHEETS_ID` | URL de la hoja de cálculo |
| `WHATSAPP_API_KEY` | Portal de 360dialog (Fase 2) |

## Despliegue en VPS

```bash
bash scripts/setup.sh
sudo systemctl start scheduling-agent
sudo systemctl status scheduling-agent
```
