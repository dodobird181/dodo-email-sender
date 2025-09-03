#!/bin/bash

set -e

APP_DIR="/home/$(whoami)/Documents/github/dodo-email-sender"
APP_MODULE="main:app"
APP_PORT=8000

echo "🔧 Installing system dependencies..."
sudo apt-get update && sudo apt-get upgrade
sudo apt-get install -y python3-pip python3-venv nginx curl
echo "📦 Installing pipx..."
pip install pipx
pipx ensurepath
echo "📦 Installing Poetry..."
pipx install poetry
export PATH="$HOME/.local/bin:$PATH"

echo "🚀 Installing app with Poetry..."
cd "$APP_DIR"
poetry install

echo "🦄 Creating Gunicorn systemd service..."

SERVICE_NAME="email_sender"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

cat <<EOF | sudo tee "/etc/systemd/system/dodo_email_sender.service"
[Unit]
Description="Gunicorn instance to serve Email Sender Flask App"
After=network.target

[Service]
User=$(whoami)
Group=www-data
WorkingDirectory="/home/$(whoami)/dodo_email_sender"
ExecStart=/bin/bash -c "/home/dodob/.local/bin/poetry run gunicorn --bind 127.0.0.1:8000 main"
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "🌐 Setting up Nginx..."

NGINX_FILE="/etc/nginx/sites-available/email_sender"

sudo tee "$NGINX_FILE" > /dev/null <<EOF
server {
    listen 80;
    server_name _;  # catch all IPs

    location / {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -sf "$NGINX_FILE" /etc/nginx/sites-enabled/email_sender
sudo systemctl start nginx
sudo nginx -t && sudo systemctl reload nginx

echo "✅ Email sender is now running! Access via: http://YOUR.SERVER.IP/"
