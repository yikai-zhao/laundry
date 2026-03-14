# AWS 生产部署完整指南

本文档带你从零完成：注册域名 → AWS 基础设施搭建 → 自动部署 → 系统上线

---

## 架构总览

```
用户浏览器
    │
    ├─ staff.yourdomain.com  ──→  CloudFront → S3 (staff-app 静态文件)
    ├─ sign.yourdomain.com   ──→  CloudFront → S3 (customer-sign 静态文件)
    ├─ admin.yourdomain.com  ──→  CloudFront → S3 (admin-dashboard 静态文件)
    │
    └─ api.yourdomain.com    ──→  ALB → ECS Fargate (FastAPI 后端)
                                        │
                                        ├─ RDS PostgreSQL (数据库)
                                        └─ S3 (照片存储) ← CloudFront (照片CDN)
```

**月费用估算（弗吉尼亚北部 us-east-1）：**
- ECS Fargate 0.5 vCPU / 1 GB：~$15
- RDS db.t3.micro PostgreSQL：~$15
- ALB：~$20
- S3 + CloudFront（低流量）：~$2
- NAT Gateway：~$35
- **合计：约 $87/月**

> 💡 省钱方法：把 NAT Gateway 去掉，改用公网子网 + ECS PublicIP。对低流量应用完全够用，可省 $35/月。

---

## 第一步：准备工作（本地电脑）

### 1.1 安装工具

```bash
# macOS
brew install awscli terraform

# Windows（用 winget）
winget install -e --id Amazon.AWSCLI
winget install -e --id Hashicorp.Terraform

# 验证
aws --version      # >= 2.x
terraform --version  # >= 1.6
```

### 1.2 注册域名

推荐在 AWS Route53 直接注册（最简单，无需在注册商修改 NS 记录）：

1. 打开 [AWS Console → Route53 → Domains](https://console.aws.amazon.com/route53/domains/)
2. 搜索你想要的域名，如 `mycleaners.com`（.com 约 $13/年）
3. 点击 Register，填写联系信息，完成购买
4. 域名激活后（通常几分钟到几小时）继续下面步骤

> 如果你在 Namecheap / GoDaddy 买了域名，第四步里 Terraform 会给你 4 个 NS 地址，你需要去注册商的 DNS 设置里把 Nameservers 改成这 4 个。

### 1.3 创建 AWS IAM 用户（给自己用的部署账号）

1. 打开 [IAM Console](https://console.aws.amazon.com/iam/)
2. 创建用户 `laundry-admin`，附加策略：`AdministratorAccess`（或最小权限：见附录）
3. 创建 Access Key → 下载 CSV

```bash
aws configure
# AWS Access Key ID: <从 CSV 粘贴>
# AWS Secret Access Key: <从 CSV 粘贴>
# Default region: us-east-1
# Default output format: json

# 测试连接
aws sts get-caller-identity
```

---

## 第二步：初始化 Terraform 状态存储（只做一次）

Terraform 需要一个 S3 桶存储状态文件（不能用 Terraform 自己创建，要手动建）：

```bash
# 替换成你的 AWS 账号 ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws s3 mb s3://laundry-tf-state --region us-east-1
aws s3api put-bucket-versioning \
  --bucket laundry-tf-state \
  --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption \
  --bucket laundry-tf-state \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
```

---

## 第三步：配置 Terraform 变量

在 `infra/terraform/` 目录创建 `terraform.tfvars`（此文件已加入 .gitignore，不会提交）：

```bash
cd /workspaces/laundry/infra/terraform
cat > terraform.tfvars << 'EOF'
domain_name    = "mycleaners.com"       # 改成你的域名
db_password    = "YourStrongPassword123!"  # 自定义，最少 12 位
openai_api_key = "sk-..."               # OpenAI API Key
jwt_secret     = "your-jwt-secret-min-32-chars-here"
aws_region     = "us-east-1"
EOF
```

---

## 第四步：运行 Terraform 部署基础设施

```bash
cd /workspaces/laundry/infra/terraform

terraform init    # 下载 Provider，初始化 S3 后端（约 1 分钟）
terraform plan    # 预览将创建的资源（约 60 个）
terraform apply   # 输入 yes 确认（约 10-15 分钟）
```

**完成后记录输出的关键值：**

```bash
terraform output                              # 查看所有输出
terraform output route53_nameservers          # 如果在第三方注册商购买域名，把这4个NS填到注册商
terraform output github_actions_access_key_id     # → GitHub Secret: AWS_ACCESS_KEY_ID
terraform output -raw github_actions_secret_access_key  # → GitHub Secret: AWS_SECRET_ACCESS_KEY
terraform output ecr_repository_url           # ECR 仓库地址
terraform output s3_staff_bucket              # → GitHub Secret: S3_STAFF_BUCKET
terraform output s3_customer_bucket           # → GitHub Secret: S3_CUSTOMER_BUCKET
terraform output s3_admin_bucket              # → GitHub Secret: S3_ADMIN_BUCKET
terraform output cloudfront_staff_id          # → GitHub Secret: CF_STAFF_ID
terraform output cloudfront_customer_id       # → GitHub Secret: CF_CUSTOMER_ID
terraform output cloudfront_admin_id          # → GitHub Secret: CF_ADMIN_ID
```

---

## 第五步：配置 GitHub Secrets 和 Variables

打开你的 GitHub 仓库 → Settings → Secrets and variables → Actions

### Repository Secrets（敏感值）

| Secret 名称 | 值来源 |
|-------------|--------|
| `AWS_ACCESS_KEY_ID` | `terraform output github_actions_access_key_id` |
| `AWS_SECRET_ACCESS_KEY` | `terraform output -raw github_actions_secret_access_key` |
| `S3_STAFF_BUCKET` | `terraform output s3_staff_bucket` |
| `S3_CUSTOMER_BUCKET` | `terraform output s3_customer_bucket` |
| `S3_ADMIN_BUCKET` | `terraform output s3_admin_bucket` |
| `CF_STAFF_ID` | `terraform output cloudfront_staff_id` |
| `CF_CUSTOMER_ID` | `terraform output cloudfront_customer_id` |
| `CF_ADMIN_ID` | `terraform output cloudfront_admin_id` |

### Repository Variables（非敏感值）

| Variable 名称 | 值 |
|--------------|-----|
| `DOMAIN_NAME` | 你的域名，如 `mycleaners.com` |

---

## 第六步：首次手动推送 Docker 镜像

在 GitHub Actions 跑之前，先手动推送一个初始镜像，这样 ECS 能正常启动：

```bash
# 获取 ECR 仓库地址
ECR_URL=$(terraform -chdir=infra/terraform output -raw ecr_repository_url)
AWS_REGION=us-east-1

# 登录 ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $(echo $ECR_URL | cut -d/ -f1)

# 构建并推送
cd /workspaces/laundry
docker build -t $ECR_URL:latest ./backend/api-service
docker push $ECR_URL:latest

# 强制 ECS 重部署（拉取 latest）
aws ecs update-service \
  --cluster laundry \
  --service laundry-backend \
  --force-new-deployment \
  --region $AWS_REGION
```

---

## 第七步：域名 NS 配置（使用第三方注册商时）

如果域名在 **Route53** 购买 → 跳过此步骤，自动生效。

如果在 **Namecheap / GoDaddy** 等购买：

1. 运行 `terraform output route53_nameservers` 得到 4 个 NS 地址
2. 登录注册商控制台 → 域名管理 → 修改 Nameservers 为"自定义"
3. 填入这 4 个 NS 地址
4. DNS 传播通常 10-60 分钟，全球最多 48 小时

验证 NS 已生效：
```bash
dig NS yourdomain.com +short
# 应该看到 4 个 awsdns-XX.xxx 地址
```

---

## 第八步：触发自动部署

```bash
cd /workspaces/laundry
git add -A
git commit -m "deploy: production AWS setup"
git push origin main
```

GitHub Actions 会自动：
1. 构建 Docker 镜像 → 推送到 ECR
2. 更新 ECS 服务（蓝绿部署）
3. 构建 3 个前端（`VITE_API_BASE_URL=https://api.yourdomain.com`）
4. 同步到 S3
5. 清除 CloudFront 缓存

**查看部署进度：**
仓库 → Actions → 最新 workflow run

---

## 第九步：验证上线

```bash
# 后端健康检查
curl https://api.yourdomain.com/health
# 期望: {"status":"ok","database":"connected"}

# 查看后端日志（ECS）
aws logs tail /ecs/laundry/backend --follow --region us-east-1
```

打开浏览器访问：
- `https://staff.yourdomain.com` — 员工收衣界面
- `https://sign.yourdomain.com` — 客户签名界面  
- `https://admin.yourdomain.com` — 管理后台

首次登录账号：
- admin / admin123（⚠️ 上线后立即改密码！）
- staff / staff123（⚠️ 上线后立即改密码！）

---

## 日常运维

### 查看日志
```bash
aws logs tail /ecs/laundry/backend --follow --region us-east-1
```

### 数据库连接（需要先 SSH 到 ECS 任务或建立 bastion）
```bash
# 在本地通过 AWS Session Manager 连接
aws ecs execute-command \
  --cluster laundry \
  --task <TASK_ID> \
  --container backend \
  --interactive \
  --command "python -c \"from app.db.database import engine; print('DB OK')\""
```

### 更新后端代码
```bash
git push origin main  # 自动触发 CI/CD
```

### 数据库备份
RDS 已配置 7 天自动备份，每天凌晨 3:00 UTC 创建快照。

手动快照：
```bash
aws rds create-db-snapshot \
  --db-instance-identifier laundry-postgres \
  --db-snapshot-identifier laundry-manual-$(date +%Y%m%d) \
  --region us-east-1
```

### 扩容
如果并发量增加，调整 ECS 任务数：
```bash
aws ecs update-service \
  --cluster laundry \
  --service laundry-backend \
  --desired-count 2 \
  --region us-east-1
```

或修改 `infra/terraform/ecs.tf` 里的 `desired_count = 2` 然后 `terraform apply`。

---

## 费用优化（可选）

### 去掉 NAT Gateway（省 $32/月）

1. 修改 `infra/terraform/ecs.tf`，把 ECS 任务放到公网子网：
   ```hcl
   network_configuration {
     subnets          = aws_subnet.public[*].id  # 改为 public
     assign_public_ip = true                      # 改为 true
   }
   ```
2. 修改 `infra/terraform/vpc.tf`，删除 `aws_nat_gateway` 和对应 EIP 资源
3. `terraform apply`

### 预留实例（省 30-40%）
在 AWS Console → EC2 → Reserved Instances / Savings Plans 购买 1 年期预留，适合稳定运行的系统。

---

## 故障排查

| 问题 | 检查步骤 |
|------|----------|
| 前端空白/404 | 查看 CloudFront 分发状态，确认 S3 部署成功 |
| API 502 Bad Gateway | ECS 任务是否 Running？ALB Target Group 健康检查是否通过？ |
| API 503 Service Unavailable | ECS 任务数是否为 0？查看 ECS 事件日志 |
| 照片上传失败 | ECS 任务角色是否有 S3 权限？S3 Bucket 策略是否正确？ |
| AI 检测不工作 | OPENAI_API_KEY 是否在 ECS 任务环境变量中？查看 CloudWatch 日志 |
| 域名无法访问 | NS 记录是否已传播？`dig NS yourdomain.com` |
| SSL 证书错误 | ACM Certificate 状态是否为 Issued？DNS 验证记录是否创建？ |

---

## 附录：Terraform 最小权限（可选）

如果不想用 AdministratorAccess，以下是 Terraform 需要的最小 IAM 权限（涵盖所有资源创建）：

VPC, EC2, ECS, ECR, RDS, S3, CloudFront, Route53, ACM, IAM, CloudWatch, ELB, SecretsManager。

对于生产初始部署，建议先用 AdministratorAccess，系统稳定后再收紧权限。
