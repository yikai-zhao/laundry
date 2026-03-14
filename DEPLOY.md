# Deployment Guide — Laundry AI Inspection System

## What Gets Deployed

| Service | URL path | Purpose |
|---|---|---|
| Staff App | `staff.yourdomain.com` | Staff-facing order management |
| Customer Sign | `sign.yourdomain.com` | Customer QR code signing |
| Admin Dashboard | `admin.yourdomain.com` | Admin overview + user management |
| Backend API | `api.yourdomain.com` | REST API + AI inspection |
| PostgreSQL | Internal only | Database |

---

## Option A: Railway.app (Fastest — ~15 min)

Railway auto-deploys from GitHub with minimal config.

1. **Create account**: https://railway.app
2. **New Project** → Deploy from GitHub repo → select `yikai-zhao/laundry`
3. Railway will detect the `docker-compose.prod.yml` — configure env vars in the dashboard
4. Set environment variables (see section below)
5. Add a custom domain in Railway settings

> ⚠️ Railway free tier has sleep-after-inactivity. Use the $5/month "Hobby" plan for production.

---

## Option B: AWS EC2 (Most Control)

### 1. Launch EC2

- Instance: **t3.small** (2 vCPU, 2GB RAM) — $0.02/hr
- AMI: **Ubuntu 24.04 LTS**
- Storage: 20GB gp3 EBS
- Security Group: allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS)

### 2. Connect and Install Docker

```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
newgrp docker

# Verify
docker --version
docker compose version
```

### 3. Clone Repository

```bash
git clone https://github.com/yikai-zhao/laundry.git
cd laundry
```

### 4. Configure Environment

```bash
cp .env.production.example .env.production
nano .env.production   # Fill in all values (see below)
```

### 5. Deploy

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

### 6. Check Status

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs backend-api --tail=50
```

---

## Option C: DigitalOcean Droplet

Same as AWS EC2 but use a **$6/month Basic Droplet** (1GB RAM — upgrade to 2GB for the AI).

1. Create Ubuntu 24.04 droplet
2. Follow same steps as EC2 from step 2 above

---

## Environment Variables

Create `.env.production` (never commit this file):

```env
# Database
POSTGRES_USER=laundry
POSTGRES_PASSWORD=<generate with: openssl rand -base64 24>
POSTGRES_DB=laundry_db

# Backend Security
JWT_SECRET=<generate with: openssl rand -hex 32>
OPENAI_API_KEY=sk-proj-UrIEm4c5...  # Your OpenAI key

# CORS — list all frontend domains
CORS_ORIGINS=https://staff.yourdomain.com,https://sign.yourdomain.com,https://admin.yourdomain.com

# Frontend build-time URLs
API_BASE_URL=https://api.yourdomain.com
CUSTOMER_SIGN_BASE_URL=https://sign.yourdomain.com
```

---

## Domain Setup

### Register Domain

1. Go to **Namecheap.com** or **Cloudflare Registrar** (~$10-12/year)
2. Suggested domain: `[shopname].com` or a generic name like `laundryai.app`

### DNS Records (point to your server IP)

| Type | Name | Value |
|---|---|---|
| A | `staff` | `YOUR_SERVER_IP` |
| A | `sign` | `YOUR_SERVER_IP` |
| A | `admin` | `YOUR_SERVER_IP` |
| A | `api` | `YOUR_SERVER_IP` |

### nginx Config

Update `deploy/nginx/nginx.conf` — replace all `yourdomain.com` with your actual domain.

### SSL Certificate (HTTPS)

After DNS propagates (~5 min), run:

```bash
# On the server
docker exec laundry-nginx sh
apk add certbot certbot-nginx
certbot --nginx -d staff.yourdomain.com -d sign.yourdomain.com -d admin.yourdomain.com -d api.yourdomain.com
```

Or use Cloudflare proxy (orange cloud) for automatic HTTPS — no certbot needed.

---

## After First Deploy

1. **Change default passwords** — log into admin dashboard → Staff → Change Password
   - admin / admin123 → set a strong password
   - staff / staff123 → set a strong password

2. **Add real staff accounts** — Admin Dashboard → Staff → Add Staff

3. **Verify AI works** — Create a test order, upload a photo, check detection

---

## Backups

```bash
# Backup database
docker exec laundry-postgres pg_dump -U laundry laundry_db > backup_$(date +%Y%m%d).sql

# Backup photos
docker cp laundry-backend-api:/app/storage ./storage_backup_$(date +%Y%m%d)
```

---

## Updates

```bash
git pull
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

---

## Troubleshooting

```bash
# View all logs
docker compose -f docker-compose.prod.yml logs -f

# Restart a service
docker compose -f docker-compose.prod.yml restart backend-api

# Access database
docker exec -it laundry-postgres psql -U laundry -d laundry_db
```
