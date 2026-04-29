#!/bin/bash
# Setup completo del servidor desde cero
set -e

echo "=== Asistente de Agendamiento con IA — Setup ==="

# 1. Dependencias del sistema
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx redis-server git

# 2. Crear directorio del proyecto
sudo mkdir -p /opt/scheduling-agent
sudo chown $USER:$USER /opt/scheduling-agent

# 3. Clonar o copiar el proyecto
# git clone <tu-repo> /opt/scheduling-agent
# O copiar archivos manualmente

# 4. Entorno virtual y dependencias
cd /opt/scheduling-agent
python3.11 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 5. Crear directorios necesarios
mkdir -p logs data

# 6. Copiar .env
cp .env.example .env
echo "EDITA /opt/scheduling-agent/.env con tus credenciales reales"

# 7. Instalar servicio systemd
sudo cp scheduling-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable scheduling-agent

# 8. Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

echo ""
echo "=== Setup completo ==="
echo "1. Edita .env con tus credenciales"
echo "2. Coloca google_credentials.json en config/"
echo "3. Ejecuta: sudo systemctl start scheduling-agent"
echo "4. Registra el webhook de Telegram:"
echo "   curl https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<DOMINIO>/webhook/telegram&secret_token=<WEBHOOK_SECRET>"
