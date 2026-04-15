#!/usr/bin/env python3
"""Build a single self-contained HTML report with embedded screenshots."""

import base64, pathlib

SCREENSHOTS_DIR = pathlib.Path(__file__).parent / "screenshots"
OUTPUT = pathlib.Path(__file__).parent / "laundry-app-demo.html"


def img_b64(filename: str) -> str:
    path = SCREENSHOTS_DIR / filename
    if not path.exists():
        return ""
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/png;base64,{data}"


sections = [
    {
        "title": "1. 員工登入",
        "text": (
            "前台員工打開手機端 Staff App，輸入帳號密碼登入系統。"
            "登入後進入訂單列表頁面。<br>"
            "<b>測試帳號：</b>emily / staff123"
        ),
        "imgs": [
            ("01-staff-login.png", "登入頁面"),
            ("02-staff-login-filled.png", "填入帳號密碼"),
        ],
    },
    {
        "title": "2. 訂單列表",
        "text": (
            "登入後看到所有訂單。頂部統計欄顯示今日訂單數、等待簽名數、待取件數等關鍵指標。"
            "每張訂單卡片包含客戶姓名、衣物件數、狀態標籤和日期。"
            "點擊任意訂單進入詳情。"
        ),
        "imgs": [("03-staff-order-list.png", "訂單列表")],
    },
    {
        "title": "3. 建立新訂單",
        "text": (
            "點擊頂部導覽列「+ New」進入新訂單頁。"
            "選擇已有客戶或新增客戶，填寫備註（如「Delicate fabric, hand clean preferred」），"
            "選擇取送方式（In-Store Dropoff / Home Pickup）和付款方式"
            "（Cash、Card、WeChat、Alipay 等），然後建立訂單。"
        ),
        "imgs": [("09-staff-new-order.png", "新訂單頁面")],
    },
    {
        "title": "4. 訂單詳情 — 衣物檢查",
        "text": (
            "進入訂單詳情頁。頂部有 7 步進度條，標示當前所在環節。"
            "顯示客戶資訊和訂單總金額。"
            "每件衣物以獨立卡片呈現，包含類型、單價、清洗方式標籤、"
            "顏色、品牌、備註。<br><br>"
            "衣物卡片中間展示正面和背面照片。"
            "下方三個操作按鈕：Camera（拍照）、Gallery（從相簿選）、Re-detect（調用 GPT-4o Vision 自動識別瑕疵）。"
        ),
        "imgs": [
            ("04-staff-order-detail-top.png", "訂單頂部 — 進度條與客戶資訊"),
            ("05-staff-order-garments.png", "衣物卡片 — 照片、瑕疵、操作按鈕"),
            ("08-staff-order-detail-full.png", "訂單詳情完整頁面"),
        ],
    },
    {
        "title": "5. 瑕疵記錄",
        "text": (
            "每件衣物下方的「Issues Found」區域列出所有檢測到的瑕疵。每條記錄包含：<br>"
            "<ul>"
            "<li><b>類型：</b>Stain（污漬）、Wear（磨損）、Missing Button（紐扣缺失）、Tear（破損）、Hole（破洞）</li>"
            "<li><b>嚴重程度：</b>Minor（輕微）/ Moderate（中等）/ Severe（嚴重）</li>"
            "<li><b>來源：</b>AI（自動檢測）/ Manual（手動添加）</li>"
            "<li><b>描述：</b>具體位置和狀況，如「Front chest area, left side — coffee stain approximately 3cm diameter」</li>"
            "</ul>"
            "員工可以 Edit（編輯）、刪除或「+ Add Issue Manually」手動新增瑕疵。"
        ),
        "imgs": [("06-staff-photos-issues.png", "瑕疵清單與 QR Code")],
    },
    {
        "title": "6. 客戶確認 QR Code",
        "text": (
            "衣物檢查完成後，頁面底部自動生成 QR Code。"
            "員工讓客戶用手機掃碼，或者直接把手機遞給客戶查看確認頁。"
            "QR Code 下方顯示完整的確認連結。"
        ),
        "imgs": [("07-staff-qr-section.png", "QR Code 確認區域")],
    },
    {
        "title": "7. 檢查報告",
        "text": (
            "點擊「Print Report」生成正式檢查報告。"
            "報告包含訂單編號、客戶資訊、每件衣物的完整記錄："
            "清洗方式標籤、面料、品牌、照片（正反面）、"
            "以及問題明細表格（類型、嚴重程度、位置描述、來源）。"
        ),
        "imgs": [("11-staff-inspection-report.png", "檢查報告")],
    },
    {
        "title": "8. 收據",
        "text": (
            "收據頁面顯示 Laundry Receipt 標題、客戶姓名電話、"
            "衣物明細表格（品名、單價）、合計金額，"
            "以及「Issues Found」匯總（共幾項問題，各自描述）。"
        ),
        "imgs": [("10-staff-receipt.png", "收據")],
    },
    {
        "title": "9. 客戶確認頁（Customer Sign 端）",
        "text": (
            "客戶掃碼後進入確認頁面，標題為「Garment Inspection Report」。"
            "頁面依序顯示：<br>"
            "<ol>"
            "<li>訂單基本資訊（客戶名、日期、備註、件數、問題總數）</li>"
            "<li>每件衣物的正反面照片</li>"
            "<li>該衣物檢測到的問題（類型 + 嚴重程度 + 具體描述）</li>"
            "<li>簽名區域 — 輸入姓名 + 手寫簽名 Canvas</li>"
            "<li>「Confirm & Sign」確認按鈕</li>"
            "</ol>"
            "客戶在觸控螢幕或滑鼠上簽名，確認後訂單狀態變更為已確認。"
        ),
        "imgs": [
            ("12-customer-confirm-top.png", "客戶確認 — 頂部"),
            ("15-customer-confirm-full.png", "客戶確認 — 完整頁面（Sarah Johnson）"),
            ("16-customer-confirm-jennifer.png", "客戶確認 — Jennifer Wong"),
        ],
    },
    {
        "title": "10. 管理後台 — Dashboard",
        "text": (
            "管理員登入桌面端後台。Dashboard 頁面顯示五個統計卡片："
            "Total Orders（總訂單）、Today（今日訂單）、Awaiting Sig（等待簽名）、"
            "Confirmed（已確認）、Ready Pickup（待取件）。"
            "下方為近期訂單表格。<br>"
            "<b>測試帳號：</b>admin / admin123"
        ),
        "imgs": [
            ("17-admin-login.png", "管理員登入"),
            ("18-admin-dashboard.png", "Dashboard 總覽"),
        ],
    },
    {
        "title": "11. 管理後台 — 訂單管理",
        "text": (
            "All Orders 頁面列出所有訂單，支持按客戶名搜索和按狀態篩選。"
            "每行顯示客戶名、件數、備註、狀態標籤和日期。"
            "點擊訂單進入詳情頁，可查看衣物照片、問題列表（紅色背景高亮）和客戶確認狀態。"
        ),
        "imgs": [
            ("19-admin-orders.png", "訂單列表"),
            ("20-admin-order-detail.png", "訂單詳情"),
        ],
    },
    {
        "title": "12. 管理後台 — 客戶管理",
        "text": (
            "Customers 頁面以表格形式展示所有客戶：姓名、電話、Email、建立日期。"
            "支持按姓名或電話搜索。"
        ),
        "imgs": [("21-admin-customers.png", "客戶列表")],
    },
    {
        "title": "13. 管理後台 — 員工管理",
        "text": (
            "Staff Management 頁面列出所有帳號，顯示姓名、角色標籤（admin / staff）、使用者名稱。"
            "可以新增員工（+ Add Staff）、修改密碼、刪除帳號。"
            "Admin 帳號僅顯示「Change Password」，不可刪除。"
        ),
        "imgs": [("22-admin-staff.png", "員工管理")],
    },
]

# ────────────────────── HTML Template ──────────────────────

html_parts = [
    """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vancouver Laundry App — 系統展示</title>
<style>
  :root { --brand: #334155; --accent: #6366f1; --bg: #f8fafc; --card: #fff; --border: #e2e8f0; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
         color: #1e293b; background: var(--bg); line-height: 1.6; }
  .container { max-width: 1100px; margin: 0 auto; padding: 40px 24px 80px; }

  /* Header */
  .header { text-align: center; margin-bottom: 48px; padding-bottom: 32px; border-bottom: 2px solid var(--border); }
  .header h1 { font-size: 28px; font-weight: 700; color: var(--brand); }
  .header p { color: #64748b; margin-top: 8px; font-size: 15px; }

  /* Table of contents */
  .toc { background: var(--card); border: 1px solid var(--border); border-radius: 8px;
         padding: 24px 32px; margin-bottom: 48px; }
  .toc h2 { font-size: 18px; margin-bottom: 12px; color: var(--brand); }
  .toc ol { padding-left: 20px; }
  .toc li { margin-bottom: 4px; }
  .toc a { color: var(--accent); text-decoration: none; }
  .toc a:hover { text-decoration: underline; }

  /* Flow diagram */
  .flow { background: var(--card); border: 1px solid var(--border); border-radius: 8px;
          padding: 24px 32px; margin-bottom: 48px; text-align: center; }
  .flow h2 { font-size: 18px; margin-bottom: 16px; color: var(--brand); text-align: left; }
  .flow-steps { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; align-items: center; }
  .flow-step { background: #eef2ff; color: #4338ca; padding: 8px 16px; border-radius: 6px;
               font-size: 13px; font-weight: 500; white-space: nowrap; }
  .flow-arrow { color: #94a3b8; font-size: 18px; }

  /* Section */
  .section { margin-bottom: 56px; }
  .section h2 { font-size: 22px; font-weight: 600; color: var(--brand); margin-bottom: 12px;
                padding-bottom: 8px; border-bottom: 1px solid var(--border); }
  .section .desc { margin-bottom: 20px; color: #334155; font-size: 15px; }
  .section .desc ul, .section .desc ol { padding-left: 20px; margin-top: 6px; }
  .section .desc li { margin-bottom: 4px; }

  /* Image grid */
  .img-grid { display: flex; flex-wrap: wrap; gap: 20px; }
  .img-card { flex: 1 1 320px; max-width: 520px; background: var(--card);
              border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
  .img-card img { width: 100%; display: block; }
  .img-card .cap { padding: 8px 12px; font-size: 13px; color: #64748b;
                   border-top: 1px solid var(--border); text-align: center; }

  /* Account table */
  .acct-table { width: 100%; border-collapse: collapse; margin-bottom: 32px; font-size: 14px; }
  .acct-table th, .acct-table td { text-align: left; padding: 8px 14px; border: 1px solid var(--border); }
  .acct-table th { background: #f1f5f9; color: var(--brand); font-weight: 600; }

  /* Sample data table */
  .data-table { width: 100%; border-collapse: collapse; margin-bottom: 32px; font-size: 14px; }
  .data-table th, .data-table td { text-align: left; padding: 8px 14px; border: 1px solid var(--border); }
  .data-table th { background: #f1f5f9; color: var(--brand); font-weight: 600; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }
  .badge-yellow { background: #fef3c7; color: #92400e; }
  .badge-green  { background: #dcfce7; color: #166534; }
  .badge-blue   { background: #dbeafe; color: #1e40af; }
  .badge-gray   { background: #f1f5f9; color: #475569; }

  /* Footer */
  .footer { text-align: center; margin-top: 48px; padding-top: 24px;
            border-top: 1px solid var(--border); color: #94a3b8; font-size: 13px; }

  @media print {
    .section { page-break-inside: avoid; }
    .img-card img { max-height: 600px; object-fit: contain; }
  }
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>Vancouver Laundry App — AI Garment Inspection System</h1>
  <p>系統展示文件 &middot; 2026-04-15</p>
</div>

<!-- TOC -->
<div class="toc">
  <h2>目錄</h2>
  <ol>
"""
]

for i, sec in enumerate(sections, 1):
    slug = f"s{i}"
    html_parts.append(f'    <li><a href="#{slug}">{sec["title"]}</a></li>\n')

html_parts.append("""  </ol>
</div>

<!-- Flow diagram -->
<div class="flow">
  <h2>核心業務流程</h2>
  <div class="flow-steps">
    <span class="flow-step">客戶送衣</span><span class="flow-arrow">→</span>
    <span class="flow-step">建立訂單</span><span class="flow-arrow">→</span>
    <span class="flow-step">拍照（正/反面）</span><span class="flow-arrow">→</span>
    <span class="flow-step">AI 自動檢測瑕疵</span><span class="flow-arrow">→</span>
    <span class="flow-step">員工複核/手動補充</span><span class="flow-arrow">→</span>
    <span class="flow-step">生成 QR Code</span><span class="flow-arrow">→</span>
    <span class="flow-step">客戶掃碼確認</span><span class="flow-arrow">→</span>
    <span class="flow-step">手寫簽名</span><span class="flow-arrow">→</span>
    <span class="flow-step">清洗處理</span><span class="flow-arrow">→</span>
    <span class="flow-step">通知取件</span>
  </div>
</div>

<!-- System overview -->
<div class="section">
  <h2>系統概覽</h2>
  <div class="desc">
    <p>系統由三個前端應用和一個後端 API 組成，通過 Nginx 反向代理統一在同一域名下。</p>
  </div>
  <table class="acct-table">
    <tr><th>應用</th><th>使用者</th><th>裝置</th><th>路徑</th></tr>
    <tr><td>Staff App</td><td>前台員工</td><td>手機 / 平板</td><td>/</td></tr>
    <tr><td>Customer Sign</td><td>客戶</td><td>手機（掃碼）</td><td>/sign/</td></tr>
    <tr><td>Admin Dashboard</td><td>管理員</td><td>桌面電腦</td><td>/admin/</td></tr>
    <tr><td>Backend API</td><td>—</td><td>—</td><td>/api/v1/</td></tr>
  </table>
  <table class="acct-table">
    <tr><th>角色</th><th>帳號</th><th>密碼</th></tr>
    <tr><td>管理員</td><td>admin</td><td>admin123</td></tr>
    <tr><td>員工 — Emily Chen</td><td>emily</td><td>staff123</td></tr>
    <tr><td>員工 — David Wang</td><td>david</td><td>staff123</td></tr>
  </table>
</div>

<!-- Sample data -->
<div class="section">
  <h2>樣例數據</h2>
  <table class="data-table">
    <tr><th>客戶</th><th>電話</th><th>訂單狀態</th><th>衣物</th><th>問題數</th></tr>
    <tr>
      <td>Sarah Johnson</td><td>+1-604-555-1234</td>
      <td><span class="badge badge-yellow">Awaiting Sig</span></td>
      <td>suit_jacket, shirt</td><td>4</td>
    </tr>
    <tr>
      <td>Michael Lee</td><td>+1-604-555-5678</td>
      <td><span class="badge badge-green">Ready Pickup</span></td>
      <td>dress_pants</td><td>2</td>
    </tr>
    <tr>
      <td>Jennifer Wong</td><td>+1-778-555-9012</td>
      <td><span class="badge badge-yellow">Awaiting Sig</span></td>
      <td>silk_blouse</td><td>2</td>
    </tr>
    <tr>
      <td>Robert Kim</td><td>+1-604-555-3456</td>
      <td><span class="badge badge-gray">Picked Up</span></td>
      <td>winter_coat</td><td>1</td>
    </tr>
    <tr>
      <td>Lisa Zhang</td><td>+1-778-555-7890</td>
      <td><span class="badge badge-blue">Inspecting</span></td>
      <td>evening_dress, cashmere_sweater</td><td>2</td>
    </tr>
  </table>
</div>

""")

# Sections
for i, sec in enumerate(sections, 1):
    slug = f"s{i}"
    html_parts.append(f'<div class="section" id="{slug}">\n')
    html_parts.append(f'  <h2>{sec["title"]}</h2>\n')
    html_parts.append(f'  <div class="desc">{sec["text"]}</div>\n')
    if sec["imgs"]:
        html_parts.append('  <div class="img-grid">\n')
        for fname, caption in sec["imgs"]:
            b64 = img_b64(fname)
            if b64:
                html_parts.append(
                    f'    <div class="img-card">'
                    f'<img src="{b64}" alt="{caption}" loading="lazy">'
                    f'<div class="cap">{caption}</div></div>\n'
                )
        html_parts.append("  </div>\n")
    html_parts.append("</div>\n\n")

html_parts.append("""
<div class="footer">
  Vancouver Laundry App &middot; AI Garment Inspection System &middot; 2026
</div>

</div><!-- .container -->
</body>
</html>
""")

OUTPUT.write_text("".join(html_parts), encoding="utf-8")
size_mb = OUTPUT.stat().st_size / 1024 / 1024
print(f"Done → {OUTPUT}  ({size_mb:.1f} MB)")
