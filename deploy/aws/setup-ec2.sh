#!/bin/bash
# ==============================================
# Laundry AI — EC2 Server Setup Script
# Run on a fresh Ubuntu 22.04/24.04 EC2 instance
# ==============================================
set -e

echo "🔧 Installing Docker..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER

echo "🔧 Installing Certbot for SSL..."
sudo apt-get install -y certbot

echo "✅ Docker and Certbot installed. Log out and back in for group changes."
echo ""
echo "Next steps:"
echo "  1. Clone the repo:  git clone <your-repo-url> /opt/laundry"
echo "  2. cd /opt/laundry"
echo "  3. cp .env.production.example .env"
echo "  4. Edit .env with real values"
echo "  5. docker compose -f docker-compose.prod.yml up -d --build"
echo "  6. Set up SSL with: sudo certbot certonly --standalone -d api.yourdomain.com -d staff.yourdomain.com -d sign.yourdomain.com -d admin.yourdomain.com"
