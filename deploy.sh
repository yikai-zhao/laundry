#!/usr/bin/env bash
######################################################################
# deploy.sh — Full AWS deployment script for dryclean.synmodel.com
#
# Prerequisites:
#   - AWS CLI v2 configured (aws configure)
#   - Terraform >= 1.6 installed
#   - Docker installed
#   - Node.js >= 20 installed
#   - Domain synmodel.com DNS accessible (for NS delegation)
#
# Usage:
#   # First time — full infrastructure + app deploy
#   ./deploy.sh init
#
#   # Subsequent deploys — just app code
#   ./deploy.sh app
#
#   # Backend only
#   ./deploy.sh backend
#
#   # Frontend only
#   ./deploy.sh frontend
#
#   # Show status
#   ./deploy.sh status
######################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)" 2>/dev/null || ROOT_DIR="$SCRIPT_DIR"
# If this script is in the project root
[[ -f "$ROOT_DIR/package.json" ]] || ROOT_DIR="$SCRIPT_DIR"

TF_DIR="$ROOT_DIR/infra/terraform"
BACKEND_DIR="$ROOT_DIR/backend/api-service"
DOMAIN="dryclean.synmodel.com"
AWS_REGION="us-east-1"
APP_NAME="dryclean"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*" >&2; }
info() { echo -e "${CYAN}[→]${NC} $*"; }

check_prerequisites() {
    local missing=0
    for _cmd in aws terraform docker node npm; do
        if ! command -v "$_cmd" &>/dev/null; then
            err "Missing: $_cmd"
            missing=1
        fi
    done
    if [[ $missing -eq 1 ]]; then
        err "Install missing prerequisites and try again."
        exit 1
    fi
    log "All prerequisites found."
}

# ─── Terraform Init ────────────────────────────
terraform_init() {
    info "Creating Terraform state S3 bucket..."
    aws s3api create-bucket \
        --bucket "${APP_NAME}-synmodel-tf-state" \
        --region "$AWS_REGION" 2>/dev/null || true
    aws s3api put-bucket-versioning \
        --bucket "${APP_NAME}-synmodel-tf-state" \
        --versioning-configuration Status=Enabled 2>/dev/null || true

    info "Initializing Terraform..."
    cd "$TF_DIR"
    terraform init -reconfigure

    info "Running Terraform plan..."
    terraform plan -out=tfplan

    echo ""
    warn "Review the plan above. Continue? (yes/no)"
    read -r confirm
    if [[ "$confirm" != "yes" ]]; then
        err "Aborted."
        exit 1
    fi

    terraform apply tfplan
    rm -f tfplan

    echo ""
    log "Infrastructure created!"
    echo ""
    info "IMPORTANT: Set up DNS delegation for $DOMAIN"
    echo "   Add these NS records to your synmodel.com DNS:"
    terraform output -json route53_nameservers | jq -r '.[]'
    echo ""
    info "Then run: $0 app"
}

# ─── Deploy Backend ────────────────────────────
deploy_backend() {
    info "Building backend Docker image..."
    cd "$TF_DIR"
    local ECR_URL
    ECR_URL=$(terraform output -raw ecr_repository_url)
    local ACCOUNT_ID
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

    info "Logging into ECR..."
    aws ecr get-login-password --region "$AWS_REGION" \
        | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

    info "Building image..."
    cd "$BACKEND_DIR"
    docker build -t "$ECR_URL:latest" -t "$ECR_URL:$(git rev-parse --short HEAD 2>/dev/null || echo 'manual')" .

    info "Pushing image to ECR..."
    docker push "$ECR_URL:latest"
    docker push "$ECR_URL:$(git rev-parse --short HEAD 2>/dev/null || echo 'manual')" 2>/dev/null || true

    info "Triggering ECS rolling deployment..."
    aws ecs update-service \
        --cluster "$APP_NAME" \
        --service "${APP_NAME}-backend" \
        --force-new-deployment \
        --region "$AWS_REGION" \
        

    log "Backend deployed! ECS will roll out the new image within ~2 minutes."
}

# ─── Deploy Frontends ──────────────────────────
deploy_frontend() {
    cd "$TF_DIR"
    local API_URL="https://api.${DOMAIN}"
    local SIGN_URL="https://sign.${DOMAIN}"

    declare -A BUCKETS=(
        ["staff-app"]=$(terraform output -raw s3_staff_bucket)
        ["customer-sign"]=$(terraform output -raw s3_customer_bucket)
        ["admin-dashboard"]=$(terraform output -raw s3_admin_bucket)
    )
    declare -A CF_DISTS=(
        ["staff-app"]=$(terraform output -raw cloudfront_staff_id)
        ["customer-sign"]=$(terraform output -raw cloudfront_customer_id)
        ["admin-dashboard"]=$(terraform output -raw cloudfront_admin_id)
    )

    for app in staff-app customer-sign admin-dashboard; do
        info "Building $app..."
        cd "$ROOT_DIR/frontend/$app"

        npm ci --silent
        # For AWS subdomain deployment, each app lives at root "/"
        VITE_API_BASE_URL="$API_URL" \
        VITE_CUSTOMER_SIGN_BASE_URL="$SIGN_URL" \
        VITE_BASE_PATH="/" \
        VITE_ROUTER_BASE="/" \
        npm run build

        info "Deploying $app to S3..."
        aws s3 sync dist/ "s3://${BUCKETS[$app]}/" \
            --delete \
            --cache-control "max-age=31536000,immutable" \
            --exclude "index.html"

        aws s3 cp dist/index.html "s3://${BUCKETS[$app]}/index.html" \
            --cache-control "no-cache,no-store,must-revalidate"

        info "Invalidating CloudFront for $app..."
        aws cloudfront create-invalidation \
            --distribution-id "${CF_DISTS[$app]}" \
            --paths "/*" \
             > /dev/null

        log "$app deployed."
    done
}

# ─── Status Check ──────────────────────────────
show_status() {
    cd "$TF_DIR"
    echo ""
    echo "═══════════════════════════════════════════"
    echo "  Dryclean Inspection System — Status"
    echo "═══════════════════════════════════════════"
    echo ""
    echo "  🌐 Staff App:     https://staff.${DOMAIN}"
    echo "  👤 Customer Sign: https://sign.${DOMAIN}"
    echo "  🔧 Admin Panel:   https://admin.${DOMAIN}"
    echo "  🔌 API:           https://api.${DOMAIN}"
    echo "  📖 API Docs:      https://api.${DOMAIN}/docs"
    echo ""

    info "Checking ECS service..."
    aws ecs describe-services \
        --cluster "$APP_NAME" \
        --services "${APP_NAME}-backend" \
        --query 'services[0].{status:status,running:runningCount,desired:desiredCount,deployments:length(deployments)}' \
        --output table \
         2>/dev/null || warn "ECS service not found"

    info "Checking API health..."
    curl -sf "https://api.${DOMAIN}/health" 2>/dev/null \
        && log "API is healthy!" \
        || warn "API health check failed (may still be deploying)"
    echo ""
}

# ─── Main ──────────────────────────────────────
main() {
    local cmd="${1:-help}"

    check_prerequisites

    case "$cmd" in
        init)
            terraform_init
            deploy_backend
            deploy_frontend
            show_status
            ;;
        app)
            deploy_backend
            deploy_frontend
            show_status
            ;;
        backend)
            deploy_backend
            ;;
        frontend)
            deploy_frontend
            ;;
        status)
            show_status
            ;;
        *)
            echo "Usage: $0 {init|app|backend|frontend|status}"
            echo ""
            echo "  init      — First-time: create AWS infra + deploy everything"
            echo "  app       — Deploy backend + all frontends"
            echo "  backend   — Deploy backend only"
            echo "  frontend  — Deploy frontends only"
            echo "  status    — Show deployment URLs and health checks"
            exit 1
            ;;
    esac
}

main "$@"
