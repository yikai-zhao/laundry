# Laundry AI Inspection System

全可执行详细设计方案稿 V1

## 1. 项目定义

### 1.1 项目名称

- 英文：Laundry AI Inspection System
- 中文：干洗店 AI 验衣系统

### 1.2 项目类型

- B2B 垂直行业业务系统（非消费类识图 App）

### 1.3 第一阶段产品形态

- Web-first，不做原生 App
- 三个前端端：
  - Staff Web App（店员）
  - Customer Signature Page（客户签字）
  - Admin Dashboard（店长/管理后台）
- 两个服务端：
  - Backend API
  - AI Detection Service

## 2. 核心目标

解决门店收衣中的四类问题：

1. 衣物原始问题无记录
2. 店员检查不标准
3. 洗后责任争议
4. 证据链不可追溯

核心闭环：

收衣 → 拍照 → AI识别 → 人工确认 → 客户签字 → 留档

## 3. MVP 范围

### 3.1 必做

- Staff Web App：登录、订单创建、客户管理、衣物项、拍照上传、AI结果查看、问题编辑、验衣结果页、二维码签字、订单列表/详情
- Customer Signature Page：扫码进入、查看照片与问题、输入姓名、电子签字、提交确认
- Admin Dashboard：登录、订单列表/详情、客户信息、照片与问题记录
- Backend API：鉴权、客户/订单/衣物/图片/验衣/问题/确认/签字
- AI Detection Service：图片任务接收、基础瑕疵识别、结构化结果输出

### 3.2 不做

- 原生 iOS/Android
- 洗后复检、客诉工单、报表中心
- 多租户 SaaS 管理界面
- 自动定价、完整 OCR、自动清洗方案推荐

## 4. 技术选型

### 4.1 前端

- React + TypeScript + Vite
- React Router
- Zustand
- Axios
- Tailwind CSS

前端目录：

- `frontend/staff-app`
- `frontend/customer-sign`
- `frontend/admin-dashboard`

### 4.2 后端与 AI

- Backend API：Python 3.11 / FastAPI / SQLAlchemy 2.x / Pydantic / Alembic
- AI Service：FastAPI / PyTorch / OpenCV / YOLOv8/YOLO11 / ONNX Runtime（后续）

### 4.3 基础设施

- PostgreSQL 15+
- Redis
- 文件存储：开发本地、生产 S3
- Docker / Docker Compose / Nginx

## 5. 系统架构

```text
Users
 ├─ Staff Web App
 ├─ Customer Signature Page
 └─ Admin Dashboard

Frontend Layer
 ├─ React + TypeScript
 └─ Axios API Calls

Backend Layer
 ├─ Backend API (FastAPI)
 ├─ AI Detection Service (FastAPI)
 └─ Async Worker (Phase 1.5 Optional)

Data Layer
 ├─ PostgreSQL
 ├─ Redis
 └─ S3 / Local Storage

Infrastructure
 ├─ Docker Compose
 ├─ Nginx
 └─ Linux / AWS
```

## 6. 业务流程

### 6.1 收衣验衣流程

店员登录 → 创建订单 → 选择/新建客户 → 添加衣物项 → 上传照片 → 触发AI检测 → 查看结果 → 编辑问题项 → 生成验衣页 → 客户扫码签字 → 订单状态更新为 `confirmed`

### 6.2 客户确认流程

扫码 → 查看订单与问题 → 输入姓名 → 手写签字 → 提交确认 → 系统归档确认记录

## 7. 页面与模块拆分

### 7.1 Staff Web App 页面

1. Login
2. Order List
3. Create Order
4. Add Garment
5. Inspection
6. Issue Editing
7. Inspection Summary
8. Order Detail

### 7.2 Customer Signature 页面

1. Inspection Review
2. Signature
3. Success

### 7.3 Admin Dashboard 页面

1. Login
2. Dashboard Home
3. Orders
4. Order Detail
5. Customers

## 8. 后端服务设计

### 8.1 Backend API 目录

```text
backend/api-service/
├─ app/
│  ├─ api/
│  ├─ core/
│  ├─ db/
│  ├─ models/
│  ├─ schemas/
│  ├─ services/
│  ├─ repositories/
│  ├─ utils/
│  └─ main.py
├─ alembic/
├─ tests/
├─ requirements.txt
└─ Dockerfile
```

### 8.2 AI Service 目录

```text
ai-service/
├─ app/
│  ├─ api/
│  ├─ models/
│  ├─ services/
│  ├─ detectors/
│  ├─ preprocess/
│  ├─ postprocess/
│  └─ main.py
├─ model_weights/
├─ tests/
├─ requirements.txt
└─ Dockerfile
```

## 9. 数据库设计范围（MVP 12 表）

1. tenant
2. store
3. app_user
4. customer
5. laundry_order
6. laundry_order_item
7. garment_photos
8. inspection_record
9. inspection_issue
10. inspection_ai_result
11. customer_confirmation
12. signature_record

关系主链：

`customer -> laundry_order -> laundry_order_item -> inspection_record -> inspection_issue / inspection_ai_result -> customer_confirmation -> signature_record`

## 10. API 范围（MVP）

### Auth

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Customers

- `GET /api/v1/customers`
- `POST /api/v1/customers`
- `GET /api/v1/customers/{id}`

### Orders

- `GET /api/v1/orders`
- `POST /api/v1/orders`
- `GET /api/v1/orders/{id}`

### Garments / Photos / Inspections / Confirmations

- `POST /api/v1/orders/{id}/items`
- `GET /api/v1/order-items/{id}`
- `POST /api/v1/order-items/{id}/photos`
- `GET /api/v1/order-items/{id}/photos`
- `POST /api/v1/order-items/{id}/inspection`
- `GET /api/v1/inspections/{id}`
- `POST /api/v1/inspections/{id}/detect`
- `POST /api/v1/inspections/{id}/issues`
- `PUT /api/v1/issues/{id}`
- `DELETE /api/v1/issues/{id}`
- `GET /api/v1/confirmations/{token}`
- `POST /api/v1/confirmations/{token}/submit`

## 11. AI 模块设计

### 11.1 输入

- 一张或多张衣物照片
- `inspection_id`
- `order_item_id`

### 11.2 输出（结构化）

```json
[
  {
    "issue_type": "stain",
    "severity_level": 2,
    "position_desc": "front lower right",
    "bbox_x": 0.42,
    "bbox_y": 0.60,
    "bbox_w": 0.12,
    "bbox_h": 0.10,
    "confidence_score": 0.91
  }
]
```

### 11.3 第一阶段检测类别

- stain
- tear
- hole
- wear

### 11.4 执行流程

读取图片 → 预处理(resize/normalize) → 模型推理 → bbox后处理 → 业务字段映射 → 保存 `inspection_ai_result` → 同步写 `inspection_issue`

## 12. 文件存储策略

开发目录：

```text
storage/
├─ raw/
├─ annotated/
└─ signatures/
```

生产 S3 路径建议：

- `/orders/{order_id}/items/{item_id}/raw/`
- `/orders/{order_id}/items/{item_id}/annotated/`
- `/confirmations/{confirmation_id}/signatures/`

## 13. 状态设计

### 13.1 订单状态

- `created`
- `inspection_pending`
- `inspection_completed`
- `awaiting_customer_confirmation`
- `confirmed`

### 13.2 验衣状态

- `pending`
- `detecting`
- `reviewing`
- `completed`

### 13.3 客户确认状态

- `pending`
- `signed`
- `expired`

## 14. 安全设计

必做：

- JWT 鉴权
- 密码哈希存储
- 文件签名 URL / 受控访问
- 随机不可预测确认 token
- 关键动作操作日志

后续增强：

- 限流
- IP 白名单
- 审计日志检索

## 15. 落地实施计划（建议）

### Sprint 1（1-2 周）

- 项目初始化、鉴权、客户/订单/衣物基础 CRUD
- 本地文件上传
- 三个前端基础路由与登录页

### Sprint 2（1-2 周）

- 验衣记录、问题项编辑
- AI 检测接入（Mock + 最小真实推理）
- 客户签字页与提交确认

### Sprint 3（1 周）

- 管理后台关键查询
- 证据链详情页
- 部署脚本、稳定性与安全补强
