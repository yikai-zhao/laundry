/**
 * Capture AI-focused screenshots highlighting the technology differentiators.
 * Focus: bounding boxes, confidence scores, AI badges, detection flow, annotated images.
 */
const { chromium } = require("playwright");
const fs = require("fs");

const SEED = JSON.parse(fs.readFileSync("/workspaces/laundry/demo/seed_output.json", "utf8"));
const DIR = "/workspaces/laundry/demo/screenshots-ai";
fs.mkdirSync(DIR, { recursive: true });

const MOBILE = { width: 430, height: 932 };
const DESKTOP = { width: 1440, height: 900 };

async function run() {
  const browser = await chromium.launch({ headless: true, args: ["--no-sandbox"] });

  // ══════════════════════════════════════
  // PART 1: STAFF APP — AI DETECTION FLOW
  // ══════════════════════════════════════
  console.log("\n═══ Staff App — AI Detection Showcase ═══");
  const staffCtx = await browser.newContext({ viewport: MOBILE });
  const sp = await staffCtx.newPage();
  await sp.goto("http://localhost/", { waitUntil: "networkidle" });

  // Login
  await sp.locator("label:has-text('Username') + input, label:has-text('Username') ~ input").first().fill("emily");
  await sp.locator('input[type="password"]').first().fill("staff123");
  await sp.click('button[type="submit"]');
  await sp.waitForURL("**/orders**", { timeout: 10000 });
  await sp.waitForTimeout(800);

  // Go to Sarah Johnson's order (the AI showcase order)
  const orderId = SEED.orders[0].id;
  await sp.goto(`http://localhost/orders/${orderId}`, { waitUntil: "networkidle" });
  await sp.waitForTimeout(1000);

  // ── Screenshot 1: Order detail with AI-detected issues, badges, confidence scores ──
  console.log("  01: Order detail — AI issues overview");
  await sp.screenshot({ path: `${DIR}/01-ai-order-overview.png`, fullPage: false });

  // Scroll to garment 1 (shirt) — focus on issues with AI badges + confidence
  console.log("  02: Shirt — AI detection results");
  // Find the first garment card issues section
  const garment1 = sp.locator("text=Issues Found").first();
  await garment1.scrollIntoViewIfNeeded();
  await sp.waitForTimeout(500);
  await sp.screenshot({ path: `${DIR}/02-ai-shirt-issues.png`, fullPage: false });

  // ── Screenshot 3: Full order page showing all AI-detected issues ──
  console.log("  03: Full order — all garments with AI results");
  await sp.screenshot({ path: `${DIR}/03-ai-full-order.png`, fullPage: true });

  // ── Screenshot 4: Click on photo to show annotated lightbox with bounding boxes ──
  console.log("  04: Annotated photo lightbox with bounding boxes");
  const firstPhoto = sp.locator('img[alt=""]').first();
  await firstPhoto.scrollIntoViewIfNeeded();
  await sp.waitForTimeout(300);
  await firstPhoto.click();
  await sp.waitForTimeout(800);
  await sp.screenshot({ path: `${DIR}/04-ai-annotated-lightbox.png`, fullPage: false });
  // Close lightbox
  await sp.locator(".fixed.inset-0").first().click({ position: { x: 10, y: 10 } });
  await sp.waitForTimeout(500);

  // ── Screenshot 5: Second garment (suit_jacket) annotated view ──
  console.log("  05: Suit jacket — annotated photo");
  const suitPhotos = sp.locator('img[alt=""]');
  const suitPhoto = suitPhotos.nth(2); // 3rd photo (suit front)
  await suitPhoto.scrollIntoViewIfNeeded();
  await sp.waitForTimeout(300);
  await suitPhoto.click();
  await sp.waitForTimeout(800);
  await sp.screenshot({ path: `${DIR}/05-ai-suit-annotated.png`, fullPage: false });
  await sp.locator(".fixed.inset-0").first().click({ position: { x: 10, y: 10 } });
  await sp.waitForTimeout(500);

  // ── Screenshot 6: Scroll to QR code section at bottom ──
  console.log("  06: QR code + customer confirmation section");
  await sp.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await sp.waitForTimeout(500);
  await sp.screenshot({ path: `${DIR}/06-ai-qr-confirm.png`, fullPage: false });

  // ── Screenshot 7: Inspection report (shows all AI + manual issues in table) ──
  console.log("  07: Inspection report");
  await sp.goto(`http://localhost/orders/${orderId}/report`, { waitUntil: "networkidle" });
  await sp.waitForTimeout(800);
  await sp.screenshot({ path: `${DIR}/07-ai-inspection-report.png`, fullPage: true });

  // ── Screenshot 8: Michael Lee's coat — severe damage detection ──
  console.log("  08: Coat — severe damage AI detection");
  const o2id = SEED.orders[1].id;
  await sp.goto(`http://localhost/orders/${o2id}`, { waitUntil: "networkidle" });
  await sp.waitForTimeout(1000);
  // Scroll to issues
  const coatIssues = sp.locator("text=Issues Found").first();
  await coatIssues.scrollIntoViewIfNeeded();
  await sp.waitForTimeout(500);
  await sp.screenshot({ path: `${DIR}/08-ai-coat-severe.png`, fullPage: false });

  // ── Screenshot 9: Coat annotated photo ──
  console.log("  09: Coat — annotated overlay");
  const coatPhoto = sp.locator('img[alt=""]').first();
  await coatPhoto.scrollIntoViewIfNeeded();
  await coatPhoto.click();
  await sp.waitForTimeout(800);
  await sp.screenshot({ path: `${DIR}/09-ai-coat-annotated.png`, fullPage: false });
  await sp.locator(".fixed.inset-0").first().click({ position: { x: 10, y: 10 } });
  await sp.waitForTimeout(500);

  // ── Screenshot 10: Jennifer Wong's dress — delicate fabric detection ──
  console.log("  10: Dress — silk fabric AI detection");
  const o3id = SEED.orders[2].id;
  await sp.goto(`http://localhost/orders/${o3id}`, { waitUntil: "networkidle" });
  await sp.waitForTimeout(1000);
  const dressIssues = sp.locator("text=Issues Found").first();
  await dressIssues.scrollIntoViewIfNeeded();
  await sp.waitForTimeout(500);
  await sp.screenshot({ path: `${DIR}/10-ai-dress-detection.png`, fullPage: false });

  // ── Screenshot 11: Dress annotated lightbox ──
  console.log("  11: Dress — annotated overlay");
  const dressPhoto = sp.locator('img[alt=""]').first();
  await dressPhoto.scrollIntoViewIfNeeded();
  await dressPhoto.click();
  await sp.waitForTimeout(800);
  await sp.screenshot({ path: `${DIR}/11-ai-dress-annotated.png`, fullPage: false });
  await sp.locator(".fixed.inset-0").first().click({ position: { x: 10, y: 10 } });
  await sp.waitForTimeout(300);

  await staffCtx.close();

  // ══════════════════════════════════════
  // PART 2: CUSTOMER CONFIRMATION — AI RESULTS VIEW
  // ══════════════════════════════════════
  console.log("\n═══ Customer App — Viewing AI Results ═══");
  const custCtx = await browser.newContext({ viewport: MOBILE });
  const cp = await custCtx.newPage();

  // Sarah's confirmation
  const sarahToken = SEED.confirmations.sarah;
  await cp.goto(`http://localhost/sign/confirm/${sarahToken}`, { waitUntil: "networkidle" });
  await cp.waitForTimeout(1000);

  console.log("  12: Customer view — AI inspection report top");
  await cp.screenshot({ path: `${DIR}/12-customer-ai-report-top.png`, fullPage: false });

  console.log("  13: Customer view — full report with all AI findings");
  await cp.screenshot({ path: `${DIR}/13-customer-ai-report-full.png`, fullPage: true });

  // Scroll to signature area
  console.log("  14: Customer view — signature area");
  await cp.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await cp.waitForTimeout(500);
  await cp.screenshot({ path: `${DIR}/14-customer-signature.png`, fullPage: false });

  // Jennifer's confirmation (dress)
  const jenToken = SEED.confirmations.jennifer;
  await cp.goto(`http://localhost/sign/confirm/${jenToken}`, { waitUntil: "networkidle" });
  await cp.waitForTimeout(1000);
  console.log("  15: Jennifer — AI findings on delicate silk dress");
  await cp.screenshot({ path: `${DIR}/15-customer-dress-ai.png`, fullPage: true });

  await custCtx.close();

  // ══════════════════════════════════════
  // PART 3: ADMIN DASHBOARD — AI OVERSIGHT
  // ══════════════════════════════════════
  console.log("\n═══ Admin Dashboard — AI Monitoring ═══");
  const adminCtx = await browser.newContext({ viewport: DESKTOP });
  const ap = await adminCtx.newPage();
  await ap.goto("http://localhost/admin/", { waitUntil: "networkidle" });

  // Login
  await ap.locator('input[placeholder="Username"]').fill("admin");
  await ap.locator('input[type="password"]').fill("admin123");
  await ap.click('button[type="submit"]');
  await ap.waitForURL("**/admin/**", { timeout: 10000 });
  await ap.waitForTimeout(800);

  console.log("  16: Admin dashboard overview");
  await ap.screenshot({ path: `${DIR}/16-admin-dashboard.png`, fullPage: false });

  // Order detail
  console.log("  17: Admin — order detail with AI issues");
  await ap.goto("http://localhost/admin/orders", { waitUntil: "networkidle" });
  await ap.waitForTimeout(500);
  // Click on Sarah's order (first one)
  const firstOrder = ap.locator("text=Sarah Johnson").first();
  await firstOrder.click();
  await ap.waitForTimeout(1000);
  await ap.screenshot({ path: `${DIR}/17-admin-order-ai-detail.png`, fullPage: true });

  await adminCtx.close();
  await browser.close();

  console.log(`\n✅ All ${17} AI-focused screenshots saved to ${DIR}/`);
}

run().catch(e => { console.error(e); process.exit(1); });
