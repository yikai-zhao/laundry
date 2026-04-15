#!/bin/bash
# ==============================================
# Laundry AI — EC2 Server Setup Script
# Domain: dryclean.synmodel.com
# Run on a fresh Ubuntu 22.04/24.04 EC2 instance
# ==============================================
set -e

DOMAIN="dryclean.synmodel.com"

echo "🔧 Installing Docker..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER

echo "🔧 Installing Certbot for SSL..."
sudo apt-get install -y certbot

echo ""
echo "✅ Docker and Certbot installed."
echo ""
echo "═══════════════════════════════════════════════"
echo " Next steps (run as current user after re-login):"
echo "═══════════════════════════════════════════════"
echo ""
echo "  1. Log out and back in for docker group:"
echo "     exit && ssh -i your-key.pem ubuntu@<EC2-IP>"
echo ""
echo "  2. Clone the repo:"
echo "     git clone https://github.com/yikai-zhao/laundry.git /opt/laundry"
echo "     cd /opt/laundry"
echo ""
echo "  3. Create .env.production (see template below):"
echo "     nano .env.production"
echo ""
echo "  4. Build and start:"
echo "     docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build"
echo ""
echo "  5. Get SSL cert (stop nginx first):"
echo "     docker compose -f docker-compose.prod.yml stop nginx"
echo "     sudo certbot certonly --standalone -d ${DOMAIN}"
echo "     docker compose -f docker-compose.prod.yml start nginx"
echo ""
echo "  6. Verify: curl http://${DOMAIN}/api/v1/auth/login"
echo ""
echo "═══════════════════════════════════════════════"
echo " .env.production template:"
echo "═══════════════════════════════════════════════"
echo ""
echo "POSTGRES_USER=laundry"
echo "POSTGRES_PASSWORD=\$(openssl rand -base64 24)"
echo "POSTGRES_DB=laundry_db"
echo "JWT_SECRET=\$(openssl rand -hex 32)"
echo "OPENAI_API_KEY=sk-proj-..."
echo "CORS_ORIGINS=https://${DOMAIN},http://${DOMAIN}"
echo "API_BASE_URL="
echo "CUSTOMER_SIGN_BASE_URL=/sign"
echo ""
