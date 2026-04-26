# 溫哥華洗衣店 App — 專案使用說明

> 本文件面向門店員工、管理人員、開發/IT 人員，所有操作步驟極其具體，按實際使用場景分節。

---

## 一、系統架構快速說明

本系統由以下 6 個 Docker 容器組成，透過 Nginx 反向代理對外提供服務：

| 容器名稱 | 服務內容 | 訪問路徑 |
|---|---|---|
| `laundry-nginx` | Nginx 反向代理（80/443 端口）| 入口 |
| `laundry-backend-api` | FastAPI 後端 API（8000 端口）| `/api/v1/...` |
| `laundry-staff-app` | 店員端 React PWA | `/`（根路徑）|
| `laundry-customer-sign` | 客戶簽字端 React 頁面 | `/sign/...` |
| `laundry-admin-dashboard` | 管理後台 React 頁面 | `/admin/...` |
| `laundry-postgres` | PostgreSQL 15 數據庫 | 僅內網 |

**照片存儲**：所有上傳照片保存在 Docker Volume `photo_storage`，掛載到後端容器的 `/app/storage` 目錄，照片通過 `http://<域名>/storage/photos/<uuid>.jpg` 訪問。

---

## 二、部署啟動

### 2.1 首次啟動（本地 / 開發環境）

```bash
cd /workspaces/laundry

# 複製環境變量模板
cp .env.example .env.production   # 如果沒有此文件，手動創建（見 2.2 節）

# 啟動全部服務
docker-compose up -d --build
```

**啟動後驗證：**
```bash
# 確認所有容器都在運行
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 確認後端健康
curl http://localhost/api/v1/health
# 期望響應：{"status":"ok","database":"connected"}
```

### 2.2 環境變量說明（`.env.production`）

```env
# 數據庫密碼（自定義，生產環境務必修改）
POSTGRES_PASSWORD=your_strong_password_here

# JWT 簽名密鑰（至少 32 位隨機字符串）
JWT_SECRET=your_jwt_secret_here

# OpenAI API Key（GPT-4.1 Vision 用於 AI 驗衣）
OPENAI_API_KEY=sk-proj-xxxxx...

# 允許跨域的前端地址（多個用逗號分隔）
CORS_ORIGINS=http://localhost,https://yourdomain.com

# 可選：AWS S3 存儲（不填則使用本地文件存儲）
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=
AWS_CLOUDFRONT_DOMAIN=
```

### 2.3 生產環境（AWS EC2）

參考 [DEPLOY_AWS.md](../DEPLOY_AWS.md) 和 [deploy/aws/setup-ec2.sh](../deploy/aws/setup-ec2.sh)。

核心步驟如下：
```bash
# 1. 在 EC2 上安裝 Docker
bash deploy/aws/setup-ec2.sh

# 2. 克隆代碼並配置 .env.production
git clone <repo_url> /opt/laundry
cd /opt/laundry
vim .env.production   # 填入生產環境值

# 3. 啟動服務（使用生產編排文件）
docker-compose -f docker-compose.prod.yml up -d --build

# 4. Nginx SSL 配置（如需 HTTPS，修改 deploy/nginx/nginx.conf）
# 已有 SSL 配置模板，替換 server_name 和 ssl_certificate 路徑即可
```

### 2.4 手機 PWA 安裝（iPhone/iPad）

系統已配置為可安裝的 Progressive Web App：

1. 用 **Safari** 瀏覽器打開 `http://<服務器地址>/`（必須用 Safari，不能用 Chrome）
2. 點擊底部工具欄中間的**「分享」按鈕**（方框加箭頭圖標）
3. 向下滾動，選擇**「添加到主屏幕」**
4. 確認名稱為 "LaundryAI"，點擊**「添加」**
5. 回到主屏幕，找到紫色 App 圖標，點擊打開

> 注意：如果在局域網外訪問，需要先通過服務器公網 IP 或域名，或使用 localtunnel 建立公網隧道。

**localtunnel 快速啟動（Codespaces / 無公網環境）：**
```bash
# 在開發環境安裝 localtunnel
npm install -g localtunnel

# 啟動隧道，將本地 80 端口暴露到公網
lt --port 80 > /tmp/lt-url.txt 2>&1 &

# 查看生成的公網 URL
cat /tmp/lt-url.txt
# 輸出示例：your url is: https://witty-cats-accept.loca.lt

# 查隧道密碼（首次在手機訪問時需要輸入）
curl https://api.ipify.org
# 輸出開發服務器的公網 IP，在手機瀏覽器中用此 IP 作為密碼
```

---

## 三、賬號體系

### 3.1 默認賬號

首次啟動時，後端自動創建以下默認賬號：

| 用戶名 | 密碼 | 角色 | 權限說明 |
|---|---|---|---|
| `admin` | `admin123` | `admin` | 可訪問所有接口，可管理用戶，可查看所有訂單 |
| `staff` | `staff123` | `staff` | 可創建/查看訂單，可上傳照片，可觸發 AI 識別 |

> **安全提醒**：生產環境**必須**在首次登錄後立即修改所有默認密碼。

### 3.2 在後台管理員工賬號

**方法一：通過 Admin Dashboard 管理（推薦）**
1. 瀏覽器訪問 `http://<服務器地址>/admin/`
2. 用 `admin` 賬號登錄
3. 點擊頂部導航 **「Staff」**
4. 點擊右上角 **「+ Add Staff」** 按鈕
5. 填寫：用戶名（英文/數字）、密碼（至少 6 位）、顯示姓名（中文）、角色（`staff` 或 `admin`）
6. 點擊 **「Create」** 完成創建

**方法二：通過 Staff App 內嵌 Admin 頁**
1. 用 `admin` 賬號登錄店員端 `http://<服務器地址>/`
2. 點擊頂部導航 **「Admin」**（僅 admin 賬號可見）
3. 切換到 **「Staff」** 頁籤
4. 操作同上

### 3.3 修改密碼

**員工修改自己的密碼：**
1. 登錄 Staff App
2. 點擊 Admin 頁面的 「Staff」 頁籤 → 找到自己的記錄 → 點擊 **「Change Password」**

**管理員修改任意員工密碼：**
1. 登錄 Admin Dashboard 或 Staff App 的 Admin 頁
2. 在 Staff 列表中找到目標用戶 → 點擊 **「Change Password」**
3. 輸入新密碼（至少 6 位）→ 點擊 **「Update」**

---

## 四、日常操作流程（店員端）

### 4.1 新建收衣訂單

1. 打開店員端 `http://<服務器地址>/`，用員工賬號登錄
2. 點擊右上角 **「+ New」** 按鈕，進入新建訂單頁
3. **選擇客戶**：
   - 在搜索框輸入客戶姓名或電話，從下拉結果中點擊選中
   - 如果是新客戶：點擊 **「+ Create New Customer」**，填入姓名和電話，點擊 **「Save Customer」**
4. 選擇**取件方式**：In-Store（到店自取）或 Home Pickup（上門取件）
5. 選擇**支付方式**：Cash / Card / WeChat / Alipay / Other
6. 填寫**備注**（可選）
7. 點擊 **「Create Order」**，自動跳轉到訂單詳情頁

### 4.2 添加衣物

在訂單詳情頁中：

1. 向下滾動找到 **「Add Garment」** 按鈕（或頁面底部的添加表單）
2. 填寫衣物信息：
   - **衣物類型**：從下拉選擇（Shirt/T-Shirt/Suit Jacket/Coat/Pants/Dress 等）
   - **服務類型**：Dry Clean（乾洗）/ Water Wash（水洗）/ Luxury Care（奢護）/ Repair（修補）
   - **顏色**：如 White、Black、Blue
   - **品牌**（可選）：如 Gucci、Zara
   - **材質**（可選）：Cotton / Silk / Wool / Leather / Down / Synthetic
   - **內裡**：勾選 Has Lining
   - **單價**：輸入服務費用（如 25.00）
3. 點擊 **「Add Garment」**，衣物卡片出現在訂單中

### 4.3 拍照上傳

在衣物卡片中：

1. 找到 **「📷 Camera」** 按鈕（直接調出相機拍照）或 **「🖼 Gallery」** 按鈕（從相冊選圖）
2. 選擇拍照角度標籤（**photo label**）：
   - `front`：正面全拍（必拍）
   - `back`：背面全拍（建議必拍）
   - `detail`：局部特寫
   - `collar`：領口
   - `cuff`：袖口
   - `hem`：下擺
3. 拍完後，圖片縮略圖出現在衣物卡片中
4. 如果提示 **「⚠️ Image may be blurry」** 或 **「⚠️ Image is too dark」**，建議重新拍攝
5. 每件衣物可上傳多張，建議至少上傳正面和背面各 1 張

> **iOS 使用提示**：首次點擊 Camera/Gallery 時，Safari 會彈出「允許訪問相機/相冊」的權限詢問，請點擊「允許」。

### 4.4 觸發 AI 識別

照片上傳後：

1. 在衣物卡片中找到 **「🔍 Detect Issues」** 按鈕（或「Detect with AI」）
2. 點擊後，按鈕變為 **「⏳ Detecting...」**，狀態標籤顯示 `detecting`
3. 等待 10–60 秒（取決於照片數量和網絡狀況）
4. 識別完成後：
   - 照片上會出現彩色的邊框標注（紅色=高嚴重度，橙色=中度，黃色=低度）
   - 每個邊框對應一個問題，顯示問題類型（污渍/破洞/磨損/缺扣/拉链問題等）和嚴重程度
   - 卡片底部顯示問題清單
5. 如果識別失敗，頁面顯示 **「AI detection failed」**，可點擊 **「Re-detect」** 重試，或手動添加問題

### 4.5 查看和編輯 AI 識別結果

識別完成後，在當前衣物卡片中：

**查看問題：**
- 每個問題條目顯示：`[問題類型] - Severity: [1/2/3] - [位置描述] - [AI/Manual 標籤]`

**刪除誤判問題：**
1. 在問題條目右側點擊紅色 **「Delete」** 按鈕
2. 確認刪除（注意：目前系統不要求填寫拒絕理由，直接刪除）

**修改問題嚴重程度：**
1. 點擊問題條目右側的 **「Edit」** 按鈕（鉛筆圖標）
2. 修改 severity_level（1=輕微/2=中度/3=嚴重）
3. 可修改位置描述（如「左袖口磨損」）
4. 點擊 **「Save」** 保存

**手動新增問題（AI 漏識別）：**
1. 找到 **「+ Add Manual Issue」** 按鈕
2. 選擇問題類型：Stain（污渍）/ Tear（撕裂）/ Hole（破洞）/ Wear（磨損）/ Wrinkle（褶皺）/ Fade（褪色）/ Missing Button（缺扣）/ Zipper Issue（拉链）/ Pilling（起球）/ Other（其他）
3. 設置嚴重程度（1/2/3）
4. 可填寫位置描述
5. 點擊 **「Add Issue」** 保存

### 4.6 推進訂單狀態

在訂單詳情頁頂部的狀態時間線下方，有狀態操作按鈕：

| 當前狀態 | 操作按鈕 | 下一狀態 |
|---|---|---|
| Created（新建）| **「Start Inspection →」** | inspection_pending |
| inspection_pending（驗衣中）| **「Mark Inspection Done →」** | inspection_completed |
| inspection_completed（驗衣完成）| **「Request Customer Signature →」** | awaiting_customer_confirmation |
| confirmed（客戶已確認）| **「Mark Ready for Pickup →」** | ready_for_pickup |
| ready_for_pickup（可取件）| **「Mark as Picked Up →」** | picked_up |
| 任意狀態 | **「Cancel Order」** | cancelled |

> **注意**：點擊狀態按鈕後，頁面自動刷新，狀態時間線中當前節點高亮。

### 4.7 生成客戶確認鏈接/二維碼

當訂單進入 `awaiting_customer_confirmation` 狀態後：

1. 在訂單詳情頁找到 **「Customer Confirmation」** 區塊
2. 點擊 **「Generate Confirmation Link」** 按鈕
3. 系統生成唯一 token，顯示：
   - **二維碼**：客戶用微信/相機掃描即可訪問
   - **鏈接**：可複製後通過任意方式發給客戶（短信、微信等）
   - 鏈接格式：`http://<服務器地址>/sign/confirm/<token>`
4. 客戶打開鏈接後可查看驗衣照片和問題，填寫姓名並電子簽字確認

### 4.8 打印收據和驗衣報告

在訂單詳情頁頂部：

- **「🖨 Receipt」** 按鈕：打開收款收據頁（含客戶信息、服務明細、費用小計/折扣/總計、付款狀態）
- **「🖨 Report」** 按鈕：打開驗衣報告頁（含 AI 標注圖、問題清單、嚴重程度統計）
- 在打開的頁面中，點擊頁面右上角 **「🖨 Print Report/Receipt」** 按鈕調出打印對話框

---

## 五、客戶端操作流程

### 5.1 客戶查看驗衣記錄並簽字

客戶收到確認鏈接後：

1. 在手機瀏覽器（建議 Safari 或 Chrome）打開確認鏈接
2. 頁面展示：
   - 訂單號（UUID 縮短後三位）
   - 門店名稱（LaundryAI）
   - 每件衣物的**照片**（含 AI 標注的彩色邊框）
   - 每件衣物的**問題列表**（類型/嚴重程度/位置描述）
3. 閱讀訂單信息
4. 在頁面底部的**「Signature」**區域：
   - 在輸入框填寫姓名（Customer Name）
   - 用手指在簽字板上繪製簽名
   - 如需重畫，點擊 **「Clear」** 清除
5. 點擊 **「Confirm & Sign」** 提交
6. 頁面跳轉至感謝頁（「Thank You! Your confirmation has been received.」），可關閉

> **已簽字情況**：如果此訂單已有人簽字，頁面會顯示 「Already confirmed by [姓名]」，不提供再次簽名。

---

## 六、管理後台操作流程

### 6.1 登錄管理後台

1. 瀏覽器訪問 `http://<服務器地址>/admin/`
2. 用 `admin` 賬號（或其他 admin 角色賬號）登錄
3. 自動跳轉至 Dashboard 首頁

### 6.2 Dashboard 首頁

顯示以下統計卡片（數據實時計算）：
- **Total Orders**：所有歷史訂單總數
- **Today**：今日創建的訂單數
- **Awaiting Sig**：狀態為 `awaiting_customer_confirmation` 的訂單數（需要客戶簽字）
- **Confirmed**：客戶已簽字確認的訂單數
- **Ready Pickup**：準備好可取件的訂單數

下方顯示最近 10 條訂單列表，點擊任意訂單行跳轉至只讀訂單詳情頁。

### 6.3 訂單管理

1. 點擊頂部導航 **「Orders」**
2. 使用搜索框按客戶姓名/電話搜索
3. 使用狀態下拉篩選（All / Created / Inspecting / Inspected / Awaiting Signature / Confirmed）
4. 點擊任意訂單行查看詳情（只讀，包含衣物照片、AI 標注圖、問題清單、客戶確認狀態和簽字圖）

### 6.4 客戶管理

1. 點擊頂部導航 **「Customers」**
2. 顯示所有客戶列表（姓名、電話、郵箱、創建日期）
3. 使用搜索框按姓名/電話搜索

### 6.5 員工管理

1. 點擊頂部導航 **「Staff」**
2. 查看所有員工列表（顯示名、用戶名、角色、創建日期）
3. **添加員工**：點擊 **「+ Add Staff」** → 填寫信息 → 點擊 **「Create」**
4. **修改密碼**：找到目標員工 → **「Change Password」** → 輸入新密碼 → **「Update」**
5. **刪除員工**：找到目標員工 → **「Delete」** → 確認彈窗（不能刪除自己的賬號）

---

## 七、常見問題排查

### 7.1 AI 識別失敗（"AI detection failed after 3 retries"）

**原因 1：OPENAI_API_KEY 未配置或無效**
```bash
# 檢查後端容器的環境變量
docker exec laundry-backend-api env | grep OPENAI
# 應輸出：OPENAI_API_KEY=sk-proj-......

# 如果為空，需重啟容器並傳入正確的 Key
docker stop laundry-backend-api
docker rm laundry-backend-api
docker run -d \
  --name laundry-backend-api \
  --network laundry_default \
  -e OPENAI_API_KEY=sk-proj-你的KEY \
  -e DATABASE_URL=postgresql://postgres:密碼@laundry-postgres:5432/laundry_db \
  -e JWT_SECRET=你的JWT密鑰 \
  -e CORS_ORIGINS=http://localhost \
  -v photo_storage:/app/storage \
  laundry-backend-api
```

**原因 2：照片未成功上傳**
```bash
# 確認照片文件存在於存儲卷
docker exec laundry-backend-api ls /app/storage/photos/
# 應看到 .jpeg 或 .jpg 文件
```

**原因 3：OpenAI 服務臨時不可用**
- 等待幾分鐘後重試
- 確認 API Key 有足够余額

### 7.2 照片顯示為問號/無法加載

```bash
# 確認存儲卷掛載正確
docker inspect laundry-backend-api | grep -A5 Mounts
# 應看到 photo_storage 掛載到 /app/storage

# 確認 nginx 可以訪問照片
curl -I http://localhost/storage/photos/<照片UUID>.jpeg
# 應返回 HTTP 200 Content-Type: image/jpeg

# 如果 404：說明照片文件不在卷裡（容器重啟時未掛載卷導致的數據丟失）
# 解決：在訂單詳情頁刪除舊照片，重新拍攝上傳
```

### 7.3 無法登錄（"invalid credentials"）

```bash
# 確認後端數據庫有用戶記錄
docker exec laundry-postgres psql -U postgres -d laundry_db \
  -c "SELECT username, role FROM app_users;"

# 如果表為空，重啟後端容器，啟動腳本會自動創建 admin/staff 默認賬號
docker restart laundry-backend-api
```

### 7.4 頁面打開空白或 404

```bash
# 確認 nginx 容器在運行
docker ps | grep nginx

# 查看 nginx 日誌確認路由問題
docker logs laundry-nginx --tail 30

# 確認前端容器在運行
docker ps | grep "staff-app\|customer-sign\|admin-dashboard"
```

### 7.5 容器啟動後數據庫遷移失敗

```bash
# 查看後端啟動日誌
docker logs laundry-backend-api --tail 50

# 如果看到 "alembic.util.exc.CommandError"，手動執行遷移
docker exec laundry-backend-api alembic upgrade head
```

### 7.6 手機 PWA 安裝後打不開

- 確保用的是 Safari（iOS 上 Chrome/Firefox 不支持 PWA 安裝）
- 如果出現「無法連接到服務器」，確認手機和服務器在同一網絡，或使用公網 localtunnel URL
- 刪除主屏幕圖標，重新在 Safari 中訪問再添加

---

## 八、數據備份

### 8.1 備份數據庫

```bash
# 導出完整數據庫
docker exec laundry-postgres pg_dump -U postgres laundry_db \
  > backup_$(date +%Y%m%d_%H%M%S).sql

# 確認備份文件
ls -lh backup_*.sql
```

### 8.2 備份照片

```bash
# 導出照片卷（所有用戶上傳的照片）
docker run --rm \
  -v photo_storage:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/photos_$(date +%Y%m%d).tar.gz -C /data .

ls -lh backup/photos_*.tar.gz
```

### 8.3 恢復數據

```bash
# 恢復數據庫
docker exec -i laundry-postgres psql -U postgres laundry_db < backup_20260426.sql

# 恢復照片
docker run --rm \
  -v photo_storage:/data \
  -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/photos_20260426.tar.gz -C /data
```

---

## 九、API 接口速查

> 所有需要認證的接口需要在請求頭加入：`Authorization: Bearer <JWT_TOKEN>`

### 登錄
```
POST /api/v1/auth/login
Body: {"username": "staff", "password": "staff123"}
Response: {"access_token": "...", "token_type": "Bearer", "user": {...}}
```

### 訂單
```
GET  /api/v1/orders                    # 訂單列表（支持 ?status=&q=&skip=&limit=）
POST /api/v1/orders                    # 創建訂單
GET  /api/v1/orders/{id}               # 訂單詳情（含衣物、照片、問題）
PATCH /api/v1/orders/{id}/status        # 更新訂單狀態
POST /api/v1/orders/{id}/confirmation  # 生成客戶確認 token
POST /api/v1/orders/{id}/cancel        # 取消訂單
```

### 衣物
```
POST   /api/v1/orders/{order_id}/items    # 添加衣物
GET    /api/v1/order-items/{item_id}      # 衣物詳情
PATCH  /api/v1/order-items/{item_id}      # 更新衣物信息
DELETE /api/v1/order-items/{item_id}      # 刪除衣物
```

### 照片
```
POST   /api/v1/order-items/{item_id}/photos    # 上傳照片（multipart, 含 photo_label）
GET    /api/v1/order-items/{item_id}/photos    # 照片列表
DELETE /api/v1/order-items/{item_id}/photos/{photo_id}   # 刪除照片
GET    /storage/photos/{filename}              # 訪問照片文件（無需認證）
```

### AI 識別
```
POST /api/v1/order-items/{item_id}/inspection  # 建立 inspection 記錄
POST /api/v1/inspections/{id}/detect            # 觸發 AI 識別（202 異步）
GET  /api/v1/inspections/{id}                  # 查詢識別結果（輪詢此接口）
GET  /api/v1/inspections/{id}/annotated/{photo_id}  # 獲取 AI 標注圖（無需認證）
```

### 問題管理
```
POST   /api/v1/inspections/{id}/issues   # 手動新增問題
PUT    /api/v1/issues/{issue_id}         # 修改問題（type/severity/position）
DELETE /api/v1/issues/{issue_id}         # 刪除問題
```

### 客戶確認
```
GET  /api/v1/confirmations/{token}          # 客戶查看驗衣單（無需認證）
POST /api/v1/confirmations/{token}/submit   # 客戶提交簽字
Body: {"customer_name": "John Smith", "signature_data": "data:image/png;base64,..."}
```

### 用戶管理（需 admin）
```
GET    /api/v1/users               # 用戶列表
POST   /api/v1/users               # 創建用戶
PATCH  /api/v1/users/{id}          # 修改用戶信息（display_name/role）
PATCH  /api/v1/users/{id}/password # 修改密碼
DELETE /api/v1/users/{id}          # 刪除用戶
```

---

## 十、版本與技術棧

| 組件 | 版本 / 技術 |
|---|---|
| 後端框架 | Python 3.11 + FastAPI 0.115 |
| 數據庫 | PostgreSQL 15 |
| ORM | SQLAlchemy 2.0 + Alembic |
| AI 服務 | OpenAI GPT-4.1 Vision API |
| 前端框架 | React 18.3 + TypeScript 5.8 + Vite 5.4 |
| 樣式 | Tailwind CSS 3.4 |
| 狀態管理 | Zustand 5.0 |
| HTTP 客戶端 | Axios 1.8 |
| 容器化 | Docker + docker-compose |
| Web 服務器 | Nginx (Alpine) |
| IaC | Terraform (AWS) |
| PWA | manifest.json + Service Worker |
