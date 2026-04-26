---
title: 洗衣 App 使用說明
date: 2026-04-26
---

# 洗衣 App 使用說明

這份文檔給兩種人看：第一種是要日常操作的店員和管理員，第二種是要維護或部署這套系統的開發人員。內容按照實際使用場景寫，不是按功能模塊分類。

---

## 一、先把服務跑起來

系統用 Docker 部署，6 個容器跑在一起。先確保服務器上裝了 Docker，然後：

```bash
cd /workspaces/laundry
docker-compose up -d --build
```

跑完之後確認一下後端是否正常：

```bash
curl http://localhost/api/v1/health
# 正常返回：{"status":"ok","database":"connected"}
```

啟動前需要有一個 `.env.production` 文件，幾個必填項：

```
POSTGRES_PASSWORD=數據庫密碼（自己設，記下來）
JWT_SECRET=隨機字符串至少32位（可以用 openssl rand -hex 32 生成）
OPENAI_API_KEY=sk-proj-你的Key（沒有這個AI識別就沒法用）
CORS_ORIGINS=http://你的服務器IP或域名
```

啟動後系統有三個入口：

| 地址 | 用途 |
|---|---|
| `http://服務器地址/` | 店員 App |
| `http://服務器地址/admin/` | 管理後台 |
| `http://服務器地址/sign/confirm/<token>` | 客戶簽字頁（由系統生成鏈接）|

---

## 二、默認賬號，上線前記得改密碼

系統第一次啟動會自動建兩個賬號：

| 用戶名 | 初始密碼 | 能做什麼 |
|---|---|---|
| admin | admin123 | 管理所有訂單、管理員工賬號 |
| staff | staff123 | 日常收衣、驗衣操作 |

**這兩個密碼上線前必須改掉**，在後台 Staff 頁面可以操作。

---

## 三、店員的日常操作

### 收一件衣服的完整流程

**1. 建訂單**

登錄後點右上角的 `+ New`，搜索客戶電話或姓名，找到了直接選，沒有就點"Create New Customer"填入姓名和電話。

選一下取件方式（到店取/上門取）和支付方式，點"Create Order"就建好了。

**2. 加衣物**

一個訂單可以有多件，每件單獨驗。點「Add Garment」，選衣物類型（Shirt/Coat/Pants 之類），選服務類型（Dry Clean/Water Wash/Luxury Care/Repair），填一下單價，確認就好，顏色品牌材質都是可選的。

**3. 拍照**

衣物卡片裡有兩個按鈕，Camera 直接拍，Gallery 從相冊選。建議每件衣物至少拍正面和背面各一張，有明顯問題的地方加拍特寫。

拍完選一下角度標籤（front / back / detail / collar / cuff / hem），上傳後如果提示「圖片模糊」或「太暗」，最好重拍，這會影響 AI 識別的準確度。

iPhone 第一次用時 Safari 會問相機和相冊權限，選允許。

**4. AI 掃描**

照片上傳完，點卡片裡的「Detect Issues」。系統把照片發給 AI，一般等 15–60 秒，完成後照片上會出現彩色框，標出問題的位置和類型（紅色嚴重、橙色中度、黃色輕微）。

如果掃描失敗，頁面有提示，可以點「Re-detect」重試。實在不行就手動加問題，不影響訂單繼續走。

**5. 過一遍結果**

AI 不是百分百準確，掃完需要人工確認。

誤判的直接刪（Delete 按鈕），漏掉的點「+ Add Manual Issue」手動加，嚴重程度不對的點 Edit 改。改完就算確認了。

**6. 推進狀態**

訂單頂部有狀態線，按順序點：

Start Inspection → Mark Inspection Done → Request Customer Signature

每次點完頁面自動刷新更新狀態。

**7. 讓客戶確認**

訂單進入「等待客戶確認」後，頁面裡會出現 Customer Confirmation 區塊，點「Generate Confirmation Link」，系統生成一個二維碼和鏈接。

把這個給客戶掃一下或發過去鏈接，客戶在自己手機上看完驗衣照片和問題說明，填個名字手寫簽字，點確認就完成了。

**8. 打印收據或報告**

訂單詳情頁右上角有 Receipt（收款收據）和 Report（驗衣報告）兩個按鈕，點進去直接 Ctrl+P 打印。

---

## 四、客戶這邊怎麼操作

客戶收到鏈接後，手機上直接點開（什麼瀏覽器都行）。

頁面上看每件衣物的照片，照片上有彩色框標出問題的位置，下面有文字說明。看完在頁面底部填一下名字，用手指在簽字框裡簽名，點「Confirm & Sign」提交就好了。

如果某個訂單已經有人簽過字了，頁面會顯示「Already confirmed by 某某」，沒法再簽。

---

## 五、管理後台

瀏覽器打開 `http://服務器地址/admin/`，用 admin 賬號登錄。

**Dashboard** 頁面顯示今日新單數、待確認數、各狀態統計，下面是最近 10 條訂單。

**Orders** 可以搜索和篩選所有訂單，點進去能看每個訂單的衣物照片、AI 識別結果、客戶確認狀態（只讀，不能改）。

**Customers** 是客戶列表，支持姓名和電話搜索。

**Staff** 管理員工賬號：點「+ Add Staff」加人，填用戶名、密碼、名字、角色；Change Password 改密碼；Delete 刪人（自己的賬號刪不了）。

---

## 六、手機安裝（iOS）

想把這個 App 裝到 iPhone 主屏幕，像原生 App 一樣用：

必須用 **Safari**，Chrome 不行。打開 App 地址後點底部中間的分享按鈕，往下滑選「添加到主屏幕」，確認名稱是 LaundryAI，添加就好了。回主屏幕就能看到紫色圖標。

如果服務器不在局域網裡，手機訪問不到，可以用 localtunnel 臨時建一個公網隧道：

```bash
npm install -g localtunnel
lt --port 80 > /tmp/lt-url.txt 2>&1 &
cat /tmp/lt-url.txt          # 得到公網地址
curl https://api.ipify.org   # 這個 IP 是手機訪問時要輸入的「通行密碼」
```

---

## 七、遇到問題怎麼查

**AI 識別一直報錯**

先查 API Key 有沒有配：

```bash
docker exec laundry-backend-api env | grep OPENAI
```

輸出是空的話說明沒配，用下面的命令重建容器重新傳入正確的 Key：

```bash
docker stop laundry-backend-api && docker rm laundry-backend-api
docker run -d --name laundry-backend-api --network laundry_default \
  -e OPENAI_API_KEY=sk-proj-你的KEY \
  -e DATABASE_URL=postgresql://postgres:密碼@laundry-postgres:5432/laundry_db \
  -e JWT_SECRET=你的密鑰 \
  -e CORS_ORIGINS=http://localhost \
  -v photo_storage:/app/storage \
  laundry-backend-api
```

**照片顯示問號**

說明照片文件不在存儲卷裡了，多半是之前重建容器時沒有掛卷。確認一下：

```bash
docker exec laundry-backend-api ls /app/storage/photos/
```

文件不在就只能刪掉訂單裡的舊照片重新上傳。以後重啟服務用 `docker-compose restart`，不要用 `docker rm`，否則沒有掛卷的情況下文件就丟了。

**登錄提示密碼錯誤**

確認數據庫裡有用戶記錄：

```bash
docker exec laundry-postgres psql -U postgres -d laundry_db \
  -c "SELECT username FROM app_users;"
```

如果查出來是空的，重啟後端容器，啟動時會自動補建默認賬號。

**頁面空白**

先看 nginx 日誌，通常能看到是哪個路由出了問題：

```bash
docker logs laundry-nginx --tail 20
```

確認三個前端容器都跑著：

```bash
docker ps | grep -E "staff|admin|sign"
```

---

## 八、備份

定期把數據庫和照片備份出來，容器隨時可能因為服務器重啟丟失狀態。

```bash
# 備份數據庫
docker exec laundry-postgres pg_dump -U postgres laundry_db \
  > backup_$(date +%Y%m%d).sql

# 備份照片
docker run --rm -v photo_storage:/data -v $(pwd):/backup \
  alpine tar czf /backup/photos_$(date +%Y%m%d).tar.gz -C /data .

# 恢復數據庫（換成實際文件名）
docker exec -i laundry-postgres psql -U postgres laundry_db \
  < backup_20260426.sql
```

---

## 九、開發者參考：主要 API

所有接口都需要在請求頭帶 `Authorization: Bearer <token>`，客戶確認相關的接口除外。

```
# 認證
POST /api/v1/auth/login

# 訂單
GET  /api/v1/orders                     支持 ?status= &q=
POST /api/v1/orders
GET  /api/v1/orders/{id}
PATCH /api/v1/orders/{id}/status
POST /api/v1/orders/{id}/confirmation   生成客戶確認 token

# 衣物和照片
POST /api/v1/orders/{order_id}/items
POST /api/v1/order-items/{id}/photos    multipart 上傳，含 photo_label 字段
DELETE /api/v1/order-items/{id}

# AI 識別
POST /api/v1/order-items/{id}/inspection
POST /api/v1/inspections/{id}/detect    202 異步，需輪詢
GET  /api/v1/inspections/{id}

# 客戶確認（無需登錄）
GET  /api/v1/confirmations/{token}
POST /api/v1/confirmations/{token}/submit

# 員工管理（需 admin）
GET  /api/v1/users
POST /api/v1/users
PATCH /api/v1/users/{id}/password
```
