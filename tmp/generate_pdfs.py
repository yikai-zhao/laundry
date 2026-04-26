#!/usr/bin/env python3
"""Convert markdown docs to PDF using weasyprint + mistune."""

import sys
import os

try:
    import mistune
except ImportError:
    os.system(f"{sys.executable} -m pip install mistune -q")
    import mistune

from weasyprint import HTML, CSS

CSS_STYLE = """
/* ── 頁面設定 ── */
@page {
    size: A4;
    margin: 20mm 22mm 22mm 20mm;
    @bottom-right {
        content: counter(page) " / " counter(pages);
        font-size: 9pt;
        color: #aaa;
    }
}

/* ── 基礎 ── */
* {
    box-sizing: border-box;
}

body {
    font-family: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei',
                 'WenQuanYi Micro Hei', Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.75;
    color: #222;
    margin: 0;
    padding: 0;
    word-break: break-word;
    overflow-wrap: break-word;
}

/* ── 標題 ── */
h1 {
    font-size: 18pt;
    font-weight: 700;
    border-bottom: 2px solid #1a1a1a;
    padding-bottom: 6pt;
    margin: 0 0 18pt;
    page-break-after: avoid;
}

h2 {
    font-size: 13pt;
    font-weight: 700;
    color: #1a1a1a;
    margin: 22pt 0 6pt;
    page-break-after: avoid;
}

h3 {
    font-size: 11pt;
    font-weight: 700;
    color: #333;
    margin: 14pt 0 4pt;
    page-break-after: avoid;
}

/* ── 段落 ── */
p {
    margin: 0 0 9pt;
    orphans: 3;
    widows: 3;
}

/* ── 清單 ── */
ul, ol {
    margin: 4pt 0 9pt;
    padding-left: 18pt;
}

li {
    margin-bottom: 3pt;
    line-height: 1.7;
}

/* ── 表格 ── */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 8pt 0 14pt;
    font-size: 9.5pt;
    table-layout: fixed;
    page-break-inside: avoid;
}

th {
    background: #efefef;
    font-weight: 700;
    text-align: left;
    padding: 5pt 8pt;
    border: 1px solid #c8c8c8;
    word-break: break-all;
    line-height: 1.5;
}

td {
    padding: 5pt 8pt;
    border: 1px solid #ddd;
    vertical-align: top;
    word-break: break-all;
    line-height: 1.6;
}

tr:nth-child(even) td {
    background: #f9f9f9;
}

/* ── 代碼 ── */
code {
    font-family: 'Courier New', 'Lucida Console', monospace;
    background: #f3f3f3;
    border: 1px solid #e0e0e0;
    padding: 1pt 3pt;
    border-radius: 2pt;
    font-size: 9pt;
    word-break: break-all;
}

pre {
    background: #f5f5f5;
    border: 1px solid #ddd;
    border-left: 3px solid #888;
    border-radius: 3pt;
    padding: 8pt 10pt;
    margin: 6pt 0 12pt;
    font-size: 8.5pt;
    line-height: 1.55;
    white-space: pre-wrap;
    word-break: break-all;
    page-break-inside: avoid;
}

pre code {
    background: none;
    border: none;
    padding: 0;
    font-size: inherit;
    word-break: break-all;
}

/* ── 分隔線 ── */
hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 16pt 0;
}

/* ── 引用 ── */
blockquote {
    border-left: 3pt solid #bbb;
    margin: 8pt 0;
    padding: 3pt 12pt;
    color: #555;
    font-style: italic;
}

strong {
    font-weight: 700;
}
"""

def md_to_pdf(md_path, pdf_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Strip front-matter
    if content.startswith('---'):
        end = content.find('---', 3)
        if end != -1:
            content = content[end+3:].lstrip()

    html_body = mistune.html(content)
    full_html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"/></head>
<body>{html_body}</body>
</html>"""

    css = CSS(string=CSS_STYLE)
    HTML(string=full_html).write_pdf(pdf_path, stylesheets=[css])
    print(f"Generated: {pdf_path}")

if __name__ == '__main__':
    docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
    docs_dir = os.path.abspath(docs_dir)

    pairs = [
        ('gap_analysis_simple.md', '系統現狀評估.pdf'),
        ('usage_guide_simple.md',  '專案使用說明.pdf'),
    ]

    for md_name, pdf_name in pairs:
        md_path  = os.path.join(docs_dir, md_name)
        pdf_path = os.path.join(docs_dir, pdf_name)
        if os.path.exists(md_path):
            md_to_pdf(md_path, pdf_path)
        else:
            print(f"Not found: {md_path}")
