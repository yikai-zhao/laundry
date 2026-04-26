# 系統現狀評估：PRD 和實際代碼差在哪裡

> 文件用途：逐條比對 PRD（含「開發版 PRD」與「洗衣 AI 識別系統功能架構」兩份文件）與目前代碼庫的實際實作狀況。  
> 結論分級：✅ 已實作 | ⚠️ 部分實作 | ❌ 尚未實作

---

## 一、用戶角色對比

| PRD 角色 | PRD 權限說明 | 當前實作 | 差距說明 |
|---|---|---|---|
| 店員 Clerk | 建單、加衣物、拍照、看 AI 結果、編輯結果、提交 | ✅ `role=staff` | 功能與 PRD 一致 |
| 店長 Manager | 查本店全部訂單、復核爭議、查統計、導出 | ❌ 無此角色 | 系統目前只有 `staff` 和 `admin` 兩個角色，沒有中層 manager 角色，也沒有爭議復核功能 |
| 系統管理員 Admin | 查全部門店、管角色權限、查模型版本、配置參數、審計日誌 | ⚠️ 部分實作 | `admin` 角色可看全部訂單和管理用戶，但沒有多門店支援、無模型版本管理頁、無審計日誌頁面 |
| 後場/工廠人員 | 查看洗護要求、補充備注、提交洗後複檢 | ❌ 無此角色 | 架構中提到的後場角色完全未實作 |
| 客戶 Customer | 查看驗衣記錄、簽字確認、提交備注/異議 | ⚠️ 部分實作 | 已實作查看和簽字，但**異議功能**未實作 |

---

## 二、訂單狀態流轉對比

### PRD 定義的狀態
```
draft → inspecting → pending_customer_confirmation → confirmed → processing → completed → cancelled
異常：pending_customer_confirmation → dispute_pending → confirmed / cancelled
```

### 當前實作的狀態
```
created → inspection_pending → inspection_completed → awaiting_customer_confirmation → confirmed → ready_for_pickup → picked_up → cancelled
```

| PRD 狀態 | 當前對應狀態 | 差距 |
|---|---|---|
| `draft` | `created` | ✅ 語義相同，名稱不同 |
| `inspecting` | `inspection_pending` | ✅ 語義相同 |
| *(inspection_completed)* | `inspection_completed` | 當前多一個「驗衣完成→等待客戶確認」的中間態，PRD 沒有對應 |
| `pending_customer_confirmation` | `awaiting_customer_confirmation` | ✅ 語義相同 |
| `confirmed` | `confirmed` | ✅ 完全一致 |
| `processing`（清洗中）| ❌ 無 | 當前沒有「清洗中」狀態，直接從 confirmed 跳到 ready_for_pickup |
| `completed` | `picked_up` | ✅ 語義對應，名稱不同 |
| `cancelled` | `cancelled` | ✅ 完全一致 |
| `dispute_pending` | ❌ 無 | **爭議狀態完全未實作**，客戶無法提出異議，不存在爭議復核流程 |

---

## 三、數據模型對比

### 3.1 訂單表（Order）

| PRD 字段 | 類型 | 當前實作 | 差距 |
|---|---|---|---|
| `id` (uuid) | 主鍵 | ✅ `id` String UUID | 一致 |
| `order_no` (varchar 50) | 訂單編號 | ❌ 無 | **缺少訂單編號字段**，前端只顯示 UUID 截斷 |
| `store_id` (uuid) | 門店 ID | ❌ 無 | **沒有多門店支援**，系統目前為單門店 |
| `customer_id` (uuid, 可空) | 客戶 ID | ⚠️ `customer_id` 必填 | PRD 允許不填，當前必須先建客戶記錄 |
| `customer_name` (varchar 100) | 客戶姓名 | ✅ 存在於 customers 表 | 走關聯表 |
| `customer_phone` (varchar 30) | 客戶電話 | ✅ 存在於 customers 表 | 走關聯表 |
| `service_type` (varchar 50) | 服務類型 | ❌ 無 | service_type 在當前設計中放在**衣物層**(`order_items`)，PRD 期望在訂單層 |
| `pickup_method` (varchar 50) | 取件方式 | ✅ `pickup_type`（in_store/home_pickup）| 已實作，字段名略不同 |
| `expected_finish_date` (datetime) | 預計完成時間 | ❌ 無 | **未保存預計完成日期** |
| `status` (varchar 50) | 訂單狀態 | ✅ 已實作 | 值略有不同（見上節） |
| `notes` (text) | 訂單備注 | ✅ `note` | 已實作 |
| `created_by` (uuid) | 創建人 | ❌ 無 | **未記錄哪個員工建了訂單** |
| `payment_method` | 支付方式 | ✅ 額外實作 | PRD 未提，當前已實作 |
| `payment_status` | 支付狀態 | ✅ 額外實作 | PRD 未提，當前已實作 |
| `discount_amount` | 折扣 | ✅ 額外實作 | PRD 未提，當前已實作 |

### 3.2 衣物表（Garment）

| PRD 字段 | 類型 | 當前實作 | 差距 |
|---|---|---|---|
| `id` (uuid) | 主鍵 | ✅ | 一致 |
| `order_id` (uuid) | 訂單 ID | ✅ `order_id` | 一致 |
| `garment_no` (varchar) | 衣物編號 | ❌ 無 | 無件號，前端無法顯示「第幾件」 |
| `garment_type` (varchar) | 衣物類型 | ✅ `garment_type` | 一致 |
| `garment_color` (varchar) | 顏色 | ✅ `color` | 字段名略不同 |
| `material` (varchar) | 材質 | ✅ `fabric_type`（cotton/silk/wool/leather/down/synthetic/other）| 已實作，字段名不同 |
| `brand` (varchar) | 品牌 | ✅ `brand` | 一致 |
| `luxury_flag` (boolean) | 高價值衣物 | ❌ 無 | **缺少高價值標記**，PRD 要求奢侈品必須強制人工備注 |
| `status` (varchar) | 衣物狀態 | ❌ 無獨立 status | 衣物無 pending_photo/photo_uploaded/ai_processing 等狀態，通過關聯的 inspection_records 間接推斷 |
| `ai_status` (varchar) | AI 狀態 | ❌ 無 | AI 狀態在 inspection_records.status 中，不在衣物層 |
| `review_status` (varchar) | 人工確認狀態 | ❌ 無 | 同上，無獨立 review_status 字段 |
| 衣物服務類型 | PRD 未在衣物層明確要求 | ✅ `service_type`（額外實作）| 當前在衣物層存服務類型，比 PRD 更細粒度 |
| `has_lining` (boolean) | 是否有內裡 | ✅ 額外實作 | PRD 未提，當前已實作 |
| `unit_price` | 單價 | ✅ 額外實作 | PRD 未提，當前已實作 |

### 3.3 衣物圖片表（Garment Image）

| PRD 字段 | 當前實作 | 差距 |
|---|---|---|
| `id`, `garment_id`, `image_type` (front/back/detail) | ✅ `id`, `order_item_id`, `photo_label` | 一致，字段名略不同 |
| `image_url` (原圖地址) | ✅ `file_path` | 只保存相對路徑，不是完整 URL |
| `annotated_image_url` (標注圖地址) | ✅ `annotated_file_path` | 已實作，但標注圖通過 API 即時生成，不是預先保存的文件 |
| `width`, `height` | ❌ 未存儲 | 上傳時未保存圖片尺寸 |
| `quality_score` (decimal) | ⚠️ 返回 quality 評分，但**不存入 DB** | 質量分只在上傳 response 返回，沒有持久化 |
| `is_blurry` (boolean) | ⚠️ 同上，不入庫 | 上傳時檢測但不持久化 |
| `is_dark` (boolean) | ⚠️ 同上，不入庫 | 上傳時檢測但不持久化 |
| `uploaded_at` | ✅ `created_at` | 一致 |
| `collar/cuff/hem` 等 photo_label | ✅ 額外實作 | 當前比 PRD 更多拍攝位置選項 |

### 3.4 AI 識別結果表（AI Detection）

PRD 設計了獨立的 `ai_detections` 表保存每個異常框，**當前設計將 AI 結果和人工結果混在同一個 `inspection_issues` 表中**，通過 `source` 字段（`ai`/`manual`）區分。

| PRD 字段 | 當前實作 | 差距 |
|---|---|---|
| `issue_type` | ✅ `issue_type`（stain/tear/hole/wear/wrinkle/fade/missing_button/zipper/pilling/other）| 基本覆蓋，但 PRD 有 `loose_thread`/`deformation`/`unknown_issue` 当前沒有 |
| `subtype` | ❌ 無子類型字段 | 無法區分「油渍」vs「水渍」等子類型 |
| `bbox_x/y/w/h` (分位數) | ✅ 已實作（0.0–1.0 歸一化）| 一致 |
| `polygon` (分割輪廓) | ❌ 無 | 沒有多邊形輪廓，只有矩形框 |
| `confidence` | ✅ `confidence_score`（0.0–1.0）| 一致 |
| `severity`（low/medium/high）| ⚠️ `severity_level`（1/2/3 整數）| 語義相同但格式不同（字符串 vs 整數） |
| `source`（ai/human_added）| ✅ `source`（ai/manual）| 一致 |
| `status`（suggested/confirmed/rejected）| ❌ 無 status 字段 | 當前問題沒有「建議/確認/拒絕」三態，只有存・刪除操作 |
| `review_required` (boolean) | ❌ 無 | 無法標記「需要複核」 |
| `image_id` | ⚠️ `photo_index`（1-based 整數）| 當前只記錄圖片序號，不存 photo UUID |

### 3.5 人工確認記錄表（Garment Review）

PRD 設計了獨立的 `garment_reviews` 表，**當前沒有此表**。人工確認的動作通過 PUT/DELETE issue 實現，沒有整體的 review 記錄。

| PRD 概念 | 當前實作 | 差距 |
|---|---|---|
| `reviewer_id`（確認人）| ❌ 無 | 不記錄哪個員工做了最終確認 |
| `final_garment_type`（最終衣物類型）| ❌ 無 | 無法修改 AI 判斷的衣物類型 |
| `summary`（最終說明）| ❌ 無 | 確認後無法填寫整體備注 |
| `has_issue`（是否有異常）| ❌ 無 | 無「未發現明顯異常」勾選框 |
| `review_completed_at`（完成時間）| ❌ 無 | 不記錄確認完成時間 |

### 3.6 客戶確認表（Customer Confirmation）

| PRD 字段 | 當前實作 | 差距 |
|---|---|---|
| `customer_viewed_at` | ❌ 無 | **不記錄客戶何時打開了驗衣頁** |
| `confirmed_at` | ✅ `confirmed_at` | 一致 |
| `disputed_at` | ❌ 無 | 沒有異議時間戳 |
| `signature_url` | ✅ `signature_records.signature_data`（base64）| 存 base64數據而非 URL |
| `confirmation_status`（pending/viewed/signed/disputed）| ⚠️ `status`（pending/signed/expired）| **缺少 viewed 和 disputed 狀態** |
| `dispute_reason` | ❌ 無 | 客戶無法提出異議，也無法記錄異議原因 |
| `comment` | ❌ 無 | 客戶無法提交補充備注 |
| token 過期機制 | ❌ 已有 `expired` 狀態但無自動過期邏輯 | Token 可以被 expire 但沒有時間判斷 |

### 3.7 審計日誌表（Audit Log）

PRD 要求全面記錄所有關鍵操作的 `audit_logs` 表。**當前只有 `issue_edit_history` 表**，記錄問題字段的前後值變更。

| PRD 審計項目 | 當前實作 | 差距 |
|---|---|---|
| 訂單創建 | ❌ 未記錄 | |
| 圖片上傳 | ❌ 未記錄 | |
| AI 調用開始/完成/失敗 | ❌ 未記錄 | |
| AI 結果被修改 | ⚠️ `issue_edit_history` 記錄字段變更 | 只記錄 issue 字段改動，不記錄刪除/新增 |
| 客戶查看 | ❌ 未記錄 | |
| 客戶簽字 | ❌ 未記錄 | |
| 客戶異議 | ❌ 未實作 | |
| 訂單狀態變更 | ❌ 未記錄 | |
| Actor ID/role | ❌ 未記錄 | 不保存操作者信息 |

---

## 四、API 接口對比

### 4.1 認證接口

| PRD 設計 | 當前實作 | 差距 |
|---|---|---|
| `POST /auth/login`，字段 `account`（email/phone）| ✅ `POST /api/v1/auth/login`，字段 `username` | 字段名不同：PRD 允許 email/phone 登錄，當前只支持 username |
| 忘記密碼 | ❌ 無 | 需要 admin 手動在後台改密碼 |
| 記住賬號 | ❌ 無 | token 存 localStorage，頁面刷新保持登錄 |

### 4.2 訂單接口

| PRD 接口 | 當前實作 | 差距 |
|---|---|---|
| `POST /orders`，含 `service_type`/`expected_finish_date` | ✅ 有 `POST /orders`，但缺少上述兩字段 | 訂單層沒有服務類型和預計完成日期 |
| `GET /orders`，支持 `store_id`/`date_from`/`date_to` 篩選 | ⚠️ 有 `GET /orders`，支持 `status`/`q` | 沒有 store_id 和日期範圍篩選 |
| `POST /orders/{id}/submit`，返回客戶確認 URL | ⚠️ `POST /orders/{id}/confirmation` 生成 token | 當前需分兩步：先建 confirmation，再拼接 URL |
| 訂單 response 含 `order_no` | ❌ 無 `order_no` | |

### 4.3 衣物接口

| PRD 接口 | 當前實作 | 差距 |
|---|---|---|
| `POST /orders/{id}/garments` | ✅ `POST /orders/{id}/items` | 路徑名不同，`garments` vs `items` |
| `GET /garments/{id}` | ✅ `GET /order-items/{id}` | 一致，路徑名不同 |
| response 含 `garment_no` | ❌ 無 | |

### 4.4 圖片接口

| PRD 接口 | 當前實作 | 差距 |
|---|---|---|
| `POST /garments/{id}/images/upload` | ✅ `POST /order-items/{id}/photos` | 功能一致，路徑名不同 |
| response 含 `image_url` (絕對 URL) | ⚠️ 返回相對 `file_path` | 需拼接 base URL 才能顯示圖片 |
| response 含 `quality_score`/`is_blurry`/`is_dark` | ✅ 已實作並返回 | 但這些質量數據不持久化入庫 |

### 4.5 AI 識別接口

PRD 設計的是**異步任務模型**（POST 提交→拿 task_id→輪詢狀態），當前實作是**後台執行+輪詢 inspection 記錄**。

| PRD 設計 | 當前實作 | 差距 |
|---|---|---|
| `POST /garments/{id}/ai/analyze`，返回 `task_id` | ⚠️ `POST /inspections/{id}/detect`，202 後台執行 | 概念相同但無獨立 task 記錄，只能輪詢 inspection.status |
| `GET /ai/tasks/{task_id}`，返回詳細 AI 結果 | ⚠️ `GET /inspections/{id}`，返回 inspection+issues | 功能等效，但結構不同 |
| `GET /garments/{id}/ai/result` | ⚠️ `GET /inspections/{id}` | 功能等效 |
| AI result 含 `garment_type`（衣物類型識別）| ✅ AI 識別包含衣物類型判斷 | 已實作 |
| AI result 含 `bbox`（問題坐標）| ✅ bbox_x/y/w/h 已實作 | 一致 |
| AI result 含 `summary` | ✅ AI 返回 summary 存入 raw_result | 但前端是否顯示需確認 |
| 識別失敗後的超時/重試機制 | ⚠️ 有重試 3 次機制 | 已實作基礎重試，但失敗後的人工填入流程前端提示不完善 |

### 4.6 人工確認接口

PRD 設計了 `POST /garments/{id}/review` 接口，用 action 字段（confirm/add/reject）批量處理 AI 結果。**當前是分散操作**：

| PRD 設計 | 當前實作 | 差距 |
|---|---|---|
| 批量 confirm/add/reject issues | ❌ 無批量接口 | 每個問題需單獨 PUT 或 DELETE |
| `action=reject` 需填 reason | ❌ 無 reason 字段 | 刪除 AI 問題不記錄原因，違反 PRD 業務規則 9 |
| `final_garment_type` 修改 | ❌ 無 | 無法修改 AI 判斷的衣物類型 |
| `has_issue=false`（標記無異常）| ❌ 無 | 無「未發現明顯異常」狀態 |

### 4.7 客戶確認接口

| PRD 接口 | 當前實作 | 差距 |
|---|---|---|
| `GET /customer/orders/{token}` 查驗衣單 | ✅ `GET /confirmations/{token}` | 功能一致 |
| `POST /customer/orders/{token}/viewed`（記錄查看）| ❌ 無此接口 | 不追蹤客戶打開時間 |
| `POST /customer/orders/{token}/confirm`（簽字）| ✅ `POST /confirmations/{token}/submit` | 功能一致 |
| `POST /customer/orders/{token}/dispute`（異議）| ❌ 無此接口 | **完全缺少異議功能** |

### 4.8 後台管理接口

| PRD 接口 | 當前實作 | 差距 |
|---|---|---|
| `GET /admin/orders` 帶高級篩選 | ⚠️ `/orders` 篩選有限，無 admin 獨立前綴 | 功能部分存在 |
| `GET /admin/disputes` | ❌ 無 | 沒有爭議訂單管理 |
| `GET /admin/logs` | ❌ 無 | 沒有審計日誌接口 |
| 導出 CSV/Excel | ❌ 無 | 沒有導出功能 |

---

## 五、前端頁面對比

### 5.1 店員端（Staff App）

| PRD 頁面 | 當前實作 | 差距 |
|---|---|---|
| 登錄頁（7.1.1）| ✅ `LoginPage.tsx` | 功能一致，無「忘記密碼」 |
| 首頁/訂單列表（7.1.2）| ✅ `OrderListPage.tsx` | 有統計卡片、搜索、狀態篩選，功能基本一致 |
| 新建訂單頁（7.1.3）| ✅ `NewOrderPage.tsx` | 有客戶選擇/新建，但缺 `service_type`（訂單層）和 `expected_finish_date` |
| 衣物列表頁（7.1.4）| ⚠️ 嵌入 `OrderDetailPage.tsx` | 衣物列表嵌在訂單詳情頁而非獨立頁面 |
| 衣物拍照頁（7.1.5）| ⚠️ 嵌入 `OrderDetailPage.tsx` | 沒有獨立拍照引導頁，相機功能內嵌在訂單詳情頁 |
| AI 識別結果頁（7.1.6）| ⚠️ 嵌入 `OrderDetailPage.tsx` | 無獨立 AI 結果頁，AI 標注框直接顯示在衣物卡片裡 |
| 人工編輯頁（7.1.7）| ⚠️ 嵌入 `OrderDetailPage.tsx` | 無獨立人工編輯頁，問題的增刪改直接在卡片上操作 |
| 訂單提交成功頁（7.1.8）| ❌ 無 | 提交後只更新狀態，沒有「提交成功+二維碼」的專用頁面 |
| 訂單詳情頁（7.1.9）| ✅ `OrderDetailPage.tsx` | 功能最全的頁面，已實作大部分訂單詳情需求 |
| 收款單/收據頁 | ✅ `ReceiptPage.tsx`（額外實作）| PRD 未提，當前已實作打印格式收據 |
| 驗衣報告打印頁 | ✅ `InspectionReportPage.tsx`（額外實作）| PRD 未提，當前已實作打印格式驗衣報告 |
| 管理員內嵌頁 | ✅ `AdminPage.tsx`（額外實作）| admin 用戶可在 staff app 內查看統計和管理員工 |

### 5.2 客戶端（Customer Sign）

| PRD 頁面 | 當前實作 | 差距 |
|---|---|---|
| 客戶驗衣詳情頁（7.2.1）| ✅ `ConfirmPage.tsx`（上半部分）| 顯示衣物圖片、標注、問題說明，功能一致 |
| 客戶簽字頁（7.2.2）| ✅ `ConfirmPage.tsx`（下半部分）| 簽字板功能完整，但與詳情合在同一頁 |
| 客戶異議頁（7.2.3）| ❌ 無 | **完全未實作**，客戶無法提出異議 |

### 5.3 後台管理（Admin Dashboard）

| PRD 頁面 | 當前實作 | 差距 |
|---|---|---|
| 管理後台首頁（7.3.1）| ✅ `DashboardPage.tsx` | 有統計卡片和近期訂單，基本一致 |
| 訂單管理頁（7.3.2）| ✅ `OrdersPage.tsx` | 有搜索和狀態篩選，功能基本一致，無導出 |
| 衣物詳情頁（7.3.3）| ✅ `OrderDetailPage.tsx`（只讀）| Admin 可查看衣物圖片、AI 結果，但與 staff 頁面不同（只讀） |
| 異議處理頁（7.3.4）| ❌ 無 | **完全未實作** |
| 審計日誌頁（7.3.5）| ❌ 無 | **完全未實作** |
| 客戶管理頁 | ✅ `CustomersPage.tsx`（額外實作）| PRD 有提到客戶管理，已實作基礎列表 |
| 員工管理頁 | ✅ `StaffPage.tsx`（額外實作）| 已實作完整員工 CRUD |

---

## 六、業務規則合規對比

PRD Section 14 定義了 10 條業務規則：

| # | PRD 業務規則 | 當前是否合規 | 說明 |
|---|---|---|---|
| 1 | 一個訂單至少包含一件衣物 | ❌ 未強制 | 可以提交空訂單 |
| 2 | 一件衣物至少要有 front 圖 | ❌ 未強制 | 沒有 photo_label=front 的強制校驗 |
| 3 | 建議必須有 back 圖，若缺失需記錄 | ❌ 未實作 | 沒有 back 圖缺失的警告記錄 |
| 4 | AI 識別成功後，必須人工確認才能提交 | ❌ 未強制 | 可以直接推進狀態而不做人工確認 |
| 5 | AI 失敗時允許人工直接錄入 | ✅ 已實作 | 可以手動添加問題 |
| 6 | 客戶確認前訂單不可自動進入 processing | ✅ 符合 | 狀態推進需手動操作 |
| 7 | 高價值衣物必須強制人工備注 | ❌ 未實作 | 沒有 `luxury_flag` 字段和強制備注邏輯 |
| 8 | 所有圖片上傳後不得覆蓋原圖，只能新增版本 | ✅ 已實作 | 每次上傳都新增記錄 |
| 9 | 刪除 AI 異常必須記錄 reject reason | ❌ 未實作 | 刪除不需要填理由，無法追溯 |
| 10 | 客戶簽字後需固化當時驗衣結果快照 | ❌ 未實作 | 客戶簽字後衣物記錄仍可被修改，沒有快照機制 |

---

## 七、非功能需求對比

### 7.1 性能
| PRD 要求 | 當前狀態 |
|---|---|
| 單圖上傳 3 秒內 | ✅ 一般可達到（本地存儲） |
| AI 識別 3–10 秒 | ⚠️ 實際 GPT-4.1 Vision 可達 10–30 秒，超出 PRD 目標 |
| 列表頁 3 秒內 | ✅ 基本可達到 |

### 7.2 安全
| PRD 要求 | 當前狀態 |
|---|---|
| JWT 登錄認證 | ✅ 已實作 |
| RBAC 權限模型 | ⚠️ 只有 staff/admin 兩級，無 manager/factory 角色 |
| 圖片存儲私有或臨時簽名 URL | ❌ 當前圖片通過 `/storage/` 靜態路由無需認證即可訪問 |
| 客戶確認鏈接帶 token 且有過期機制 | ⚠️ 有 token，但無自動過期時間戳 |
| 審計日誌不可被普通店員修改 | ❌ 沒有審計日誌接口，更無權限控制 |

### 7.3 多門店/SaaS
| PRD 要求 | 當前狀態 |
|---|---|
| 多門店支援（store_id）| ❌ 未實作，單一門店設計 |
| 模型版本管理 | ❌ 未實作 |
| 統計報表/BI | ❌ 只有基礎統計卡片 |

---

## 八、架構中未提到但已額外實作的功能

以下是 PRD 中未明確要求、但開發中已額外完成的功能：

| 功能 | 說明 |
|---|---|
| 收款收據打印 | `ReceiptPage.tsx`：按訂單生成含付款信息的打印格式收據 |
| 驗衣報告打印 | `InspectionReportPage.tsx`：打印格式標注報告，含 AI 問題清單 |
| 圖片質量即時檢測 | 上傳時即時計算 blur/dark 評分並在前端警告 |
| 衣物內裡記錄 | `has_lining` 字段，PRD 未提 |
| 衣物單價+訂單總價 | 完整的計費邏輯，PRD 只有服務類型，未設計報價 |
| Payment method/status | 現金/刷卡/微信/支付寶/其他，PRD 未提 |
| Discount amount | 折扣金額字段，PRD 未提 |
| PWA 支援 | manifest.json + icons，可安裝到手機主屏幕 |
| AWS S3/CloudFront 接口 | 可選 S3 存儲，PRD 僅提到建議使用雲存儲 |
| Terraform IaC | 完整 AWS 部署腳本，PRD 未涉及 |
| 員工管理（admin）| 完整的 Staff CRUD，PRD 提到權限管理但未設計頁面細節 |
| 多種拍照角度標籤 | front/back/detail/collar/cuff/hem，PRD 只設計了前三種 |

---

## 九、優先補足清單（按 PRD P0/P1 優先級）

### P0 級（MVP 缺口，影響核心流程）

1. **客戶異議功能**：`dispute_pending` 狀態 + 客戶異議頁 + 後台異議處理頁
2. **AI 拒絕原因記錄**：刪除 AI 問題時強制填寫 reason，存入 history
3. **確認後訂單快照**：客戶簽字後鎖定訂單所有衣物記錄
4. **人工確認強制流程**：AI 完成後必須顯式確認才能推進狀態
5. **`order_no` 生成**：格式如 `ORD-20260426-0001`，用於客戶溝通

### P1 級（重要業務需求）

6. **圖片質量分入庫**：上傳時將 quality_score/is_blurry/is_dark 存入 garment_photos
7. **客戶查看時間記錄**：`customer_viewed_at` 字段和 `/viewed` 接口
8. **審計日誌**：完整 audit_logs 表，記錄訂單/圖片/AI/狀態變更
9. **奢侈品標記**：`luxury_flag` 字段和強制備注提示
10. **拍照引導流程**：獨立拍照頁，包含前/後圖強制要求

### P2 級（完善度提升）

11. **Manager 角色**：獨立的門店主管賬號和爭議復核界面
12. **多門店**：store_id 字段和多門店數據隔離
13. **導出 CSV/Excel**：後台訂單導出功能
14. **token 自動過期**：客戶確認鏈接設置過期時間（如 72 小時）
15. **圖片訪問權限控制**：照片 URL 需要 token 才可訪問

---

## 十、總結

**總體符合度評估**

| 維度 | 符合率 | 說明 |
|---|---|---|
| 核心收衣驗衣流程 | **75%** | 主流程可走通，但缺人工確認強制、快照等關鍵細節 |
| 數據模型 | **60%** | 核心字段已有，缺 order_no/store_id/luxury_flag/audit_log 等 |
| API 接口 | **65%** | 主要 CRUD 完整，缺 dispute/viewed/export/admin-log 接口 |
| 前端頁面 | **70%** | 主頁面完整，但缺獨立 AI 結果頁/異議頁/成功頁/日誌頁 |
| 業務規則合規 | **30%** | 10 條規則中只有 3 條強制實施 |
| 安全與權限 | **50%** | JWT+RBAC 基礎已有，照片訪問無鑑權、審計缺失 |

**當前系統可以支撐**：門店日常收衣、AI 驗衣、客戶電子簽字的核心業務流程。  
**當前系統不支撐**：客戶異議處理、多門店管理、操作審計追蹤、洗後複檢、數據導出。
