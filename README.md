# 🧥 Laundry AI Inspection System

**干洗店 AI 验衣系统** — B2B Web-first 生产级系统

完整业务闭环：收衣 → 拍照 → AI 识别 → 人工确认/编辑 → 生成二维码 → 客户扫码查看并签字 → 后台留档

---

## 系统架构

| 服务 | 技术栈 | 端口 | 说明 |
|------|--------|------|------|
| **Staff App** | React + TypeScript + Tailwind | 5173 | 店员操作端：接单、拍照、AI检测、编辑问题、生成确认码 |
| **Customer Sign** | React + TypeScript + Tailwind | 5174 | 客户签字端：扫码查看检衣报告，手写签名确认 |
| **Admin Dashboard** | React + TypeScript + Tailwind | 5175 | 管理后台：数据看板、订单管理、客户管理 |
| **Backend API** | Python FastAPI + SQLAlchemy | 8000 | RESTful API，JWT 认证，文件上传，GPT-4o Vision AI 检测 |
| **PostgreSQL** | PostgreSQL 15 | 5432 | 生产数据库（开发环境使用 SQLite） |

---

## 快速启动（开发环境）

### 1. 启动后端 API

```bash
cd backend/api-service
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

首次启动自动创建数据库表和默认账号。

### 2. 启动前端（3个终端）

```bash
# 终端 1：店员端
cd frontend/staff-app && npm install && npx vite --port 5173 --host

# 终端 2：客户签字端
cd frontend/customer-sign && npm install && npx vite --port 5174 --host

# 终端 3：管理后台
cd frontend/admin-dashboard && npm install && npx vite --port 5175 --host
```

### 3. 访问系统

| 入口 | 本地地址 |
|------|----------|
| 店员端 | http://localhost:5173 |
| 客户签字端 | http://localhost:5174 |
| 管理后台 | http://localhost:5175 |
| API 文档 (Swagger) | http://localhost:8000/docs |
| API 健康检查 | http://localhost:8000/health |

---

## 默认账号

| 角色 | 用户名 | 密码 | 适用入口 |
|------|--------|------|----------|
| 店员 | `staff` | `staff123` | Staff App |
| 管理员 | `admin` | `admin123` | Admin Dashboard / Staff App |

⚠️ **生产环境必须更改默认密码和 JWT 密钥！**

---

## 完整操作流程

### Step 1: 店员登录
打开 Staff App → 输入 `staff` / `staff123` → 进入订单列表页

### Step 2: 创建订单
点击 "**+ New Order**" → 搜索/创建客户 → 填写备注 → 创建订单

### Step 3: 添加衣物
在订单详情页 → 输入衣物类型(如 coat)、颜色、品牌 → 点击 Add

### Step 4: 拍照上传
点击 "📷 Upload Photos" → 选择照片上传（支持 jpg/png/webp/gif/bmp，单张 ≤10MB）

### Step 5: AI 自动检测
点击 "🤖 AI Detect" → 系统自动识别衣物问题（污渍/撕裂/破洞/磨损）
- 显示检测结果（类型、严重程度、位置、置信度）
- 支持编辑/删除 AI 检测结果
- 支持手动添加问题

### Step 6: 生成客户确认码
点击 "**Generate Customer QR Code**" → 生成二维码
- 二维码包含唯一加密 token
- 可展示给客户扫码

### Step 7: 客户扫码签字
客户扫描二维码 → 打开 Customer Sign 页面 → 查看：
- 订单信息、衣物详情、照片
- 每件衣物的检测问题列表
- 输入姓名 → 手写签名 → 点击 "Confirm & Sign"

### Step 8: 确认完成
签字成功后：
- 订单状态自动更新为 "confirmed"
- Staff App 显示签名记录
- Admin Dashboard 可查看完整历史

---

## API 端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/auth/login` | 用户登录 | ❌ |
| GET | `/api/v1/auth/me` | 当前用户信息 | ✅ |
| GET/POST | `/api/v1/customers` | 客户列表/创建（?q=搜索） | ✅ |
| GET | `/api/v1/customers/{id}` | 客户详情 | ✅ |
| GET/POST | `/api/v1/orders` | 订单列表/创建（?q=&status=） | ✅ |
| GET | `/api/v1/orders/{id}` | 订单详情（含衣物/检测/确认） | ✅ |
| POST | `/api/v1/orders/{id}/items` | 添加衣物 | ✅ |
| POST | `/api/v1/orders/{id}/confirmation` | 生成确认链接 | ✅ |
| POST | `/api/v1/order-items/{id}/photos` | 上传照片 | ✅ |
| POST | `/api/v1/order-items/{id}/inspection` | 创建检测 | ✅ |
| POST | `/api/v1/inspections/{id}/detect` | 触发 AI 检测 | ✅ |
| POST | `/api/v1/inspections/{id}/issues` | 手动添加问题 | ✅ |
| PUT/DELETE | `/api/v1/issues/{id}` | 编辑/删除问题 | ✅ |
| GET | `/api/v1/confirmations/{token}` | 获取确认详情（公开） | ❌ |
| POST | `/api/v1/confirmations/{token}/submit` | 提交签名（公开） | ❌ |

完整 Swagger 文档：`http://localhost:8000/docs`

---

## 生产部署（AWS EC2）

### 前提
- AWS EC2 实例（推荐 t3.medium 或以上，Ubuntu 22.04/24.04）
- 域名已解析到 EC2 公网 IP（需要 4 个子域名）
  - `api.yourdomain.com` → API 服务
  - `staff.yourdomain.com` → 店员端
  - `sign.yourdomain.com` → 客户签字端
  - `admin.yourdomain.com` → 管理后台

### 部署步骤

```bash
# 1. SSH 到 EC2
ssh ubuntu@your-ec2-ip

# 2. 运行安装脚本
bash deploy/aws/setup-ec2.sh

# 3. 重新登录（Docker 权限生效）
exit && ssh ubuntu@your-ec2-ip

# 4. 克隆项目
git clone <your-repo-url> /opt/laundry
cd /opt/laundry

# 5. 配置环境变量
cp .env.production.example .env
nano .env  # 修改以下内容：
#   POSTGRES_PASSWORD=<强随机密码>
#   JWT_SECRET=<64位随机字符串>
#   API_BASE_URL=https://api.yourdomain.com
#   CORS_ORIGINS=https://staff.yourdomain.com,https://sign.yourdomain.com,https://admin.yourdomain.com

# 6. 构建并启动
docker compose -f docker-compose.prod.yml up -d --build

# 7. 配置 SSL 证书
sudo certbot certonly --standalone \
  -d api.yourdomain.com \
  -d staff.yourdomain.com \
  -d sign.yourdomain.com \
  -d admin.yourdomain.com

# 8. 验证
curl https://api.yourdomain.com/health
```

### 生产环境文件结构

```
docker-compose.prod.yml    # 生产 Docker Compose（Postgres + API + 3 frontends + Nginx）
deploy/nginx/nginx.conf    # Nginx 反向代理配置（4 个子域名路由）
deploy/aws/setup-ec2.sh    # EC2 服务器初始化脚本
.env.production.example    # 生产环境变量模板
```

### Docker 服务架构

```
┌──────────┐
│  Nginx   │:80/:443
│(反向代理) │
└────┬─────┘
     │
     ├── staff.domain.com  → staff-app container
     ├── sign.domain.com   → customer-sign container
     ├── admin.domain.com  → admin-dashboard container
     └── api.domain.com    → backend-api container
                                    │
                              ┌─────┴─────┐
                              │ PostgreSQL │
                              └───────────┘
```

---

## 安全特性

- ✅ JWT 认证（8 小时过期）
- ✅ 密码哈希（PBKDF2-SHA256）
- ✅ 文件上传类型验证（仅允许图片格式）
- ✅ 文件大小限制（10MB）
- ✅ 可配置 CORS 白名单
- ✅ 客户确认使用加密随机 Token（`secrets.token_urlsafe`）
- ✅ 签名提交后防重复提交
- ✅ API 自动生成文档（Swagger UI）

---

## 技术栈

| 层级 | 技术 |
|------|------|
| Frontend | React 18 + TypeScript 5.8 + Vite 5 + Tailwind CSS 3.4 + Zustand + Axios |
| Backend | Python 3.11+ + FastAPI 0.115 + SQLAlchemy 2.0 + Pydantic 2.10 |
| Auth | python-jose (JWT) + passlib (PBKDF2) |
| Database | PostgreSQL 15（生产）/ SQLite（开发） |
| Deploy | Docker + Nginx + AWS EC2 |

---

## 目录结构

```
├── backend/api-service/         # 后端 API 服务
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── core/                # 配置、安全
│   │   ├── db/                  # 数据库连接
│   │   ├── models/              # SQLAlchemy 模型 (12 张表)
│   │   └── api/v1/routes/       # API 路由 (8 个模块)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── staff-app/               # 店员操作端 (6 页面)
│   ├── customer-sign/           # 客户签字端 (3 页面)
│   └── admin-dashboard/         # 管理后台 (5 页面)
├── deploy/
│   ├── nginx/nginx.conf         # Nginx 反向代理
│   └── aws/setup-ec2.sh         # EC2 安装脚本
├── docker-compose.yml           # 开发环境
├── docker-compose.prod.yml      # 生产环境
└── docs/executable-design-v1.md # 详细设计文档
```
