#!/usr/bin/env python3
"""Build AI-focused self-contained HTML demo report."""
import base64, pathlib

SDIR = pathlib.Path(__file__).parent / "screenshots-ai"
OUTPUT = pathlib.Path(__file__).parent / "laundry-ai-demo.html"


def img(fn):
    p = SDIR / fn
    if not p.exists(): return ""
    return f"data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}"


sections = [
    # ── Section 0: AI Technology Architecture ──
    {
        "title": "AI 識別技術方案",
        "tag": "TECH",
        "text": """
<p>本系統採用 <b>GPT-4o Vision 多模態大模型</b> 作為核心 AI 識別引擎，通過手機攝像頭（後置主鏡頭）拍攝衣物正面/反面照片，
上傳至後端服務，調用 AI 進行自動化瑕疵檢測。</p>

<div class="tech-grid">
  <div class="tech-card">
    <div class="tech-icon">📸</div>
    <h4>拍攝方式</h4>
    <p>員工使用<b>手機後置攝像頭</b>拍攝，系統自動調用 <code>capture="environment"</code> 開啟主鏡頭。
    每件衣物至少拍攝 <b>正面 + 反面</b> 兩張照片，可選補拍細節圖（領口、袖口、污漬特寫）。</p>
    <p class="tech-note">MVP 階段使用手機拍照，後期可接入 360° 旋轉拍攝架或專業光箱設備，配合固定焦距和光源，改善拍攝一致性。</p>
  </div>
  <div class="tech-card">
    <div class="tech-icon">🖼️</div>
    <h4>圖片質量控制</h4>
    <p>上傳時自動執行多維度質量檢測：</p>
    <ul>
      <li><b>模糊檢測</b> — Laplacian 方差 &lt; 50 告警</li>
      <li><b>亮度檢測</b> — 過暗（&lt;40）或過曝（&gt;240）告警</li>
      <li><b>分辨率檢測</b> — 寬/高 &lt; 300px 告警</li>
    </ul>
    <p>不合格時提示員工重拍，確保 AI 識別準確率。</p>
  </div>
  <div class="tech-card">
    <div class="tech-icon">🧠</div>
    <h4>AI 識別引擎</h4>
    <p>核心模型：<b>OpenAI GPT-4o Vision</b>（多模態大模型）</p>
    <ul>
      <li>支持同時分析最多 <b>4 張高清照片</b></li>
      <li>專業洗衣驗衣 Prompt Engineering — 20+ 年驗衣專家角色</li>
      <li>輸出結構化 JSON：瑕疵類型、嚴重程度、精確位置、置信度、定位框座標</li>
      <li>溫度 = 0，強制 JSON 格式回覆，3 次重試</li>
    </ul>
    <p class="tech-note">後期可替換為自訓練 YOLOv8/YOLO11 模型或 Landing AI 平台，降低單次調用成本。</p>
  </div>
  <div class="tech-card">
    <div class="tech-icon">🎯</div>
    <h4>檢測能力</h4>
    <p>10 種瑕疵類型 × 3 級嚴重程度：</p>
    <table class="mini-table">
      <tr><th>類型</th><th>代碼</th><th>說明</th></tr>
      <tr><td>🔴 污漬</td><td>stain</td><td>食物、油漬、墨水、紅酒、水漬、汗漬</td></tr>
      <tr><td>🔵 破損</td><td>tear</td><td>面料撕裂、脫線、開縫</td></tr>
      <tr><td>🔵 破洞</td><td>hole</td><td>蛀洞、穿刺、磨穿</td></tr>
      <tr><td>🟡 磨損</td><td>wear</td><td>面料磨薄、頻繁使用磨損</td></tr>
      <tr><td>🟠 褶皺</td><td>wrinkle</td><td>深層褶皺、需要熨燙</td></tr>
      <tr><td>🟣 褪色</td><td>fade</td><td>日曬褪色、漂白、泛黃</td></tr>
      <tr><td>🟢 缺扣</td><td>missing_button</td><td>紐扣缺失或鬆動</td></tr>
      <tr><td>🔷 拉鏈</td><td>zipper</td><td>拉鏈損壞、卡頓</td></tr>
      <tr><td>🟠 起球</td><td>pilling</td><td>面料起球</td></tr>
      <tr><td>⬜ 其他</td><td>other</td><td>其他需要關注的問題</td></tr>
    </table>
  </div>
</div>

<div class="ai-flow">
  <h4>AI 識別流程</h4>
  <div class="flow-steps">
    <span class="flow-step">員工拍照上傳</span><span class="fa">→</span>
    <span class="flow-step step-auto">圖片質量檢測</span><span class="fa">→</span>
    <span class="flow-step step-ai">GPT-4o Vision 分析</span><span class="fa">→</span>
    <span class="flow-step step-auto">結構化 JSON 解析</span><span class="fa">→</span>
    <span class="flow-step step-ai">生成定位框 (BBox)</span><span class="fa">→</span>
    <span class="flow-step">員工複核/補充</span><span class="fa">→</span>
    <span class="flow-step">標註圖覆蓋渲染</span><span class="fa">→</span>
    <span class="flow-step">客戶確認簽字</span>
  </div>
</div>
""",
        "imgs": [],
    },
    # ── Section 1: Order Overview with AI Results ──
    {
        "title": "AI 檢測結果概覽",
        "tag": "DETECT",
        "text": """<p>員工打開訂單詳情，系統展示每件衣物的 AI 識別結果。
每條瑕疵記錄清楚標示 <b>AI</b>（紫色標籤）或 <b>Manual</b>（藍色標籤）來源，
以及嚴重程度分級（Minor / Moderate / Severe）和置信度百分比。</p>
<p>這讓員工和客戶都能清楚看到<b>哪些是 AI 自動發現、哪些是員工手動補充</b>，體現系統的智能化程度。</p>""",
        "imgs": [
            ("02-ai-shirt-issues.png", "訂單概覽 — AI 標籤 + 嚴重程度 + 置信度"),
            ("08-ai-coat-severe.png", "Burberry 大衣 — AI 檢測到嚴重破損 (Severe)"),
        ],
    },
    # ── Section 2: Annotated Photo with Bounding Boxes ──
    {
        "title": "AI 標註圖：自動定位瑕疵區域",
        "tag": "BBOX",
        "text": """<p>點擊衣物照片，進入全屏查看模式。系統自動在照片上<b>繪製彩色定位框 (Bounding Box)</b>，
精確標示每個瑕疵的位置。</p>
<ul>
  <li><b>紅色框</b> — 污漬 (stain)</li>
  <li><b>黃色框</b> — 磨損 (wear)</li>
  <li><b>藍色框</b> — 破損/破洞 (tear/hole)</li>
  <li><b>紫色框</b> — 褪色 (fade)</li>
  <li><b>綠色框</b> — 缺扣 (missing_button)</li>
  <li><b>橙色框</b> — 起球/褶皺 (pilling/wrinkle)</li>
</ul>
<p>每個框標示 <b>瑕疵類型 + 嚴重程度級別</b>（如 S1=輕微, S2=中等, S3=嚴重），讓員工一目了然。</p>
<p>框座標由 AI 以歸一化浮點值返回 (0.0-1.0)，前端根據圖片實際尺寸計算像素位置，實現精確疊加。</p>""",
        "imgs": [
            ("04-ai-annotated-lightbox.png", "西裝外套 — 3 個 AI 定位框：磨損 S2 + 污漬 S1 + 缺扣 S1"),
            ("09-ai-coat-annotated.png", "冬季大衣 — 3 個 AI 定位框：褪色 S1 + 污漬 S2 + 破損 S3"),
            ("11-ai-dress-annotated.png", "絲質禮服 — AI 檢測結果疊加"),
        ],
    },
    # ── Section 3: Inspection Report ──
    {
        "title": "AI 檢查報告：結構化輸出",
        "tag": "REPORT",
        "text": """<p>系統自動匯整 AI 識別結果生成正式檢查報告，包含：</p>
<ul>
  <li>衣物照片（附帶標註框）</li>
  <li>問題明細表：類型 / 嚴重程度 / 位置描述 / AI 或手動來源</li>
  <li>每件衣物分別列出，便於員工和客戶逐一核對</li>
</ul>
<p>注意第 4 條「Stain · Minor」標示為 <b>Manual</b>（手動來源）— 這是員工在 AI 檢測後手動補充 AI 未發現的小瑕疵，
體現「<b>AI 輔助 + 人工複核</b>」的完整工作流。</p>""",
        "imgs": [
            ("07-ai-inspection-report.png", "完整檢查報告 — 包含衣物照片 + 問題表 + AI/Manual 來源標示"),
        ],
    },
    # ── Section 4: Multi-defect detection ──
    {
        "title": "多重瑕疵同時檢測",
        "tag": "MULTI",
        "text": """<p>AI 能在同一件衣物上同時檢測出<b>多種不同類型的瑕疵</b>，每種獨立標注：</p>
<ul>
  <li><b>白色襯衫</b>（Brooks Brothers）：AI 檢測出 3 個問題 — 咖啡漬 (94%)、紐扣鬆動 (87%)、領口磨損 (72%)</li>
  <li><b>深藍西裝</b>（Hugo Boss）：AI 檢測出 3 個問題 — 手肘磨損 (91%)、油漬 (83%)、背部起球 (76%)</li>
  <li><b>Burberry 大衣</b>：AI 檢測出 3 個問題 — 嚴重撕裂 (97%)、大面積食物漬 (95%)、肩部褪色 (68%)</li>
</ul>
<p>置信度越高表示 AI 越確信該瑕疵存在。低置信度（如 68%）的問題員工可以選擇刪除或確認。</p>""",
        "imgs": [
            ("03-ai-full-order.png", "Sarah Johnson 完整訂單 — 2 件衣物 7 個問題（6 AI + 1 Manual）"),
        ],
    },
    # ── Section 5: Customer AI View ──
    {
        "title": "客戶端：透明呈現 AI 檢測結果",
        "tag": "CUSTOMER",
        "text": """<p>客戶掃碼後看到的確認頁面同樣展示完整的 AI 檢測結果和標註照片，
讓客戶了解衣物洗前狀態已被<b>專業 AI 系統</b>記錄在案。</p>
<p>這不僅提升客戶信任度，也為洗後責任歸屬提供<b>可追溯的電子證據</b>。
客戶可以查看每個瑕疵的詳細描述，確認後手寫簽名。</p>""",
        "imgs": [
            ("13-customer-ai-report-full.png", "客戶確認頁 — 完整 AI 檢測結果 + 照片標註框 + 電子簽名"),
            ("15-customer-dress-ai.png", "絲質禮服客戶確認 — AI 檢測出酒漬、拉線、褶皺"),
        ],
    },
    # ── Section 6: Admin Backend ──
    {
        "title": "管理後台：AI 結果審計",
        "tag": "ADMIN",
        "text": """<p>管理員後台完整展示每個訂單的 AI 檢測結果，包括：</p>
<ul>
  <li><b>AI / Manual 來源標籤</b> — 清楚區分自動和手動識別結果</li>
  <li><b>嚴重程度等級</b> — Lv.1 (Minor) / Lv.2 (Moderate) / Lv.3 (Severe)</li>
  <li><b>置信度百分比</b> — 如 94%, 87%, 72% 等，便於質量審核</li>
  <li><b>詳細位置描述</b> — AI 輸出的精確描述（如 "Front chest area, left side — coffee stain approximately 3cm diameter"）</li>
</ul>
<p>管理員可據此監控 AI 檢測質量、評估人工修正率、統計各類瑕疵分布。</p>""",
        "imgs": [
            ("17-admin-order-ai-detail.png", "管理後台 — 訂單詳情 + AI 識別結果 + 置信度"),
            ("16-admin-dashboard.png", "Dashboard 數據總覽"),
        ],
    },
]

# ────────────── HTML ──────────────

html = ["""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vancouver Laundry App — AI 衣物識別系統技術展示</title>
<style>
:root{--brand:#1e293b;--accent:#6366f1;--bg:#f8fafc;--card:#fff;--bdr:#e2e8f0;--ai:#7c3aed;--ok:#059669}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;color:#1e293b;background:var(--bg);line-height:1.65}
.container{max-width:1100px;margin:0 auto;padding:40px 24px 80px}
code{background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:0.9em}

/* Header */
.header{text-align:center;margin-bottom:48px;padding-bottom:32px;border-bottom:2px solid var(--bdr)}
.header h1{font-size:28px;font-weight:700;color:var(--brand)}
.header .sub{font-size:15px;color:#64748b;margin-top:6px}
.header .badges{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:16px}
.badge{display:inline-flex;align-items:center;gap:4px;padding:4px 12px;border-radius:6px;font-size:12px;font-weight:600}
.badge-ai{background:#ede9fe;color:#6d28d9}.badge-vision{background:#ecfdf5;color:#047857}
.badge-bbox{background:#dbeafe;color:#1d4ed8}.badge-conf{background:#fef3c7;color:#92400e}

/* Section */
.section{margin-bottom:56px}
.section-head{display:flex;align-items:center;gap:12px;margin-bottom:14px;padding-bottom:8px;border-bottom:1px solid var(--bdr)}
.section-head h2{font-size:22px;font-weight:600;color:var(--brand);flex:1}
.tag{font-size:10px;font-weight:700;letter-spacing:1px;padding:3px 10px;border-radius:4px;background:#ede9fe;color:#6d28d9}
.desc{margin-bottom:20px;color:#334155;font-size:15px}
.desc ul,.desc ol{padding-left:20px;margin-top:6px}
.desc li{margin-bottom:3px}

/* Tech grid */
.tech-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin:20px 0}
.tech-card{background:var(--card);border:1px solid var(--bdr);border-radius:10px;padding:20px}
.tech-card h4{font-size:16px;margin:6px 0 8px;color:var(--brand)}
.tech-card p{font-size:13px;color:#475569;margin-bottom:6px}
.tech-card ul{font-size:13px;color:#475569;padding-left:18px}
.tech-card li{margin-bottom:2px}
.tech-icon{font-size:28px}
.tech-note{font-size:12px;color:#94a3b8;border-top:1px solid var(--bdr);padding-top:8px;margin-top:8px;font-style:italic}
.mini-table{width:100%;border-collapse:collapse;font-size:12px;margin-top:8px}
.mini-table th,.mini-table td{padding:4px 8px;border:1px solid var(--bdr);text-align:left}
.mini-table th{background:#f1f5f9;font-weight:600}

/* AI flow */
.ai-flow{background:var(--card);border:1px solid var(--bdr);border-radius:10px;padding:20px;margin:20px 0}
.ai-flow h4{font-size:16px;margin-bottom:12px;color:var(--brand)}
.flow-steps{display:flex;flex-wrap:wrap;align-items:center;gap:6px;justify-content:center}
.flow-step{background:#f1f5f9;padding:6px 14px;border-radius:6px;font-size:12px;font-weight:500;white-space:nowrap}
.step-ai{background:#ede9fe;color:#6d28d9;font-weight:700}
.step-auto{background:#ecfdf5;color:#047857}
.fa{color:#94a3b8;font-size:16px}

/* Image grid */
.img-grid{display:flex;flex-wrap:wrap;gap:20px}
.img-card{flex:1 1 320px;max-width:520px;background:var(--card);border:1px solid var(--bdr);border-radius:8px;overflow:hidden}
.img-card.wide{max-width:100%;flex-basis:100%}
.img-card img{width:100%;display:block}
.img-card .cap{padding:8px 12px;font-size:13px;color:#64748b;border-top:1px solid var(--bdr);text-align:center}

/* Highlight callout */
.callout{background:#ede9fe;border-left:4px solid #7c3aed;border-radius:0 8px 8px 0;padding:16px 20px;margin:20px 0;font-size:14px;color:#3b0764}
.callout b{color:#6d28d9}

/* Footer */
.footer{text-align:center;margin-top:48px;padding-top:24px;border-top:1px solid var(--bdr);color:#94a3b8;font-size:13px}

@media print{.section{page-break-inside:avoid}.img-card img{max-height:600px;object-fit:contain}}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>Vancouver Laundry App — AI 衣物識別驗衣系統</h1>
  <p class="sub">技術展示文件 — 著重呈現 AI 核心能力</p>
  <div class="badges">
    <span class="badge badge-ai">🧠 GPT-4o Vision AI</span>
    <span class="badge badge-bbox">🎯 自動定位框 BBox</span>
    <span class="badge badge-conf">📊 置信度評分</span>
    <span class="badge badge-vision">📸 圖片質量控制</span>
  </div>
</div>

<div class="callout">
  <b>核心技術優勢：</b>本系統通過手機拍照 + GPT-4o Vision 多模態 AI，自動檢測 10 種衣物瑕疵，
  輸出定位框座標、嚴重程度分級和置信度評分。員工只需拍照 → AI 自動分析 → 人工複核，
  完成從收衣到客戶確認的全流程數字化。
</div>
"""]

for i, sec in enumerate(sections):
    tag = sec.get("tag", "")
    html.append(f'<div class="section" id="s{i}">\n')
    html.append(f'  <div class="section-head"><h2>{sec["title"]}</h2>')
    if tag:
        html.append(f'<span class="tag">{tag}</span>')
    html.append('</div>\n')
    html.append(f'  <div class="desc">{sec["text"]}</div>\n')
    if sec["imgs"]:
        html.append('  <div class="img-grid">\n')
        for fn, cap in sec["imgs"]:
            b64 = img(fn)
            if not b64: continue
            wide = "wide" if len(sec["imgs"]) == 1 else ""
            html.append(f'    <div class="img-card {wide}"><img src="{b64}" alt="{cap}" loading="lazy"><div class="cap">{cap}</div></div>\n')
        html.append('  </div>\n')
    html.append('</div>\n\n')

html.append("""
<div class="callout">
  <b>拍攝方案規劃：</b>MVP 階段使用員工<b>手機後置攝像頭</b>拍攝，適合現有門店快速導入。
  後期可升級為：<br>
  ① <b>桌面式光箱 + 固定支架</b> — 標準化背景和光源，改善 AI 識別一致性<br>
  ② <b>360° 旋轉拍攝台</b> — 自動多角度拍攝，無需手動翻轉衣物<br>
  ③ <b>專用平板工作站</b> — 固定在櫃台，一體化收衣驗衣操作<br>
  AI 模型本身不需要改動，只需提高輸入圖片質量即可提升識別準確率。
</div>

<div class="footer">
  Vancouver Laundry App — AI Garment Inspection System &middot; 2026
</div>
</div>
</body>
</html>
""")

OUTPUT.write_text("".join(html), encoding="utf-8")
mb = OUTPUT.stat().st_size / 1024 / 1024
print(f"Done → {OUTPUT}  ({mb:.1f} MB)")
