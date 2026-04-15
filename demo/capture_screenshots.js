/**
 * Automated screenshot capture for Vancouver Laundry App — AI Garment Inspection System
 * Captures complete business flow: Staff login → Order management → Inspection → Customer sign → Admin dashboard
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost';
const OUT_DIR = '/workspaces/laundry/demo/screenshots';
const seedData = JSON.parse(fs.readFileSync('/workspaces/laundry/demo/seed_output.json', 'utf8'));

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });

  // ═══════════════════════════════════════
  // PART 1: STAFF APP — Mobile viewport (iPhone-like)
  // ═══════════════════════════════════════
  console.log('\n━━━ PART 1: Staff App ━━━');
  const staffCtx = await browser.newContext({
    viewport: { width: 430, height: 932 },
    deviceScaleFactor: 2,
  });
  const staff = await staffCtx.newPage();

  // 1-1: Login Page
  console.log('  📸 01 - Staff Login Page');
  await staff.goto(`${BASE_URL}/login`);
  await sleep(1500);
  await staff.screenshot({ path: `${OUT_DIR}/01-staff-login.png`, fullPage: false });

  // 1-2: Fill & Login
  console.log('  📸 02 - Staff Login Filled');
  await staff.fill('input[type="text"], input[name="username"], input[placeholder*="user" i], input:first-of-type', 'emily');
  await staff.fill('input[type="password"]', 'staff123');
  await sleep(500);
  await staff.screenshot({ path: `${OUT_DIR}/02-staff-login-filled.png`, fullPage: false });

  // Click login
  await staff.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign"), button:has-text("登")');
  await sleep(2500);

  // 1-3: Order List Page
  console.log('  📸 03 - Order List');
  await staff.screenshot({ path: `${OUT_DIR}/03-staff-order-list.png`, fullPage: true });

  // 1-4: Click into Order 1 (Sarah Johnson — has most data)
  const order1Id = seedData.orders[0].id;
  console.log('  📸 04 - Order Detail (Sarah Johnson)');
  await staff.goto(`${BASE_URL}/orders/${order1Id}`);
  await sleep(2500);
  await staff.screenshot({ path: `${OUT_DIR}/04-staff-order-detail-top.png`, fullPage: false });

  // 1-5: Scroll down to see garments
  console.log('  📸 05 - Order Garments Section');
  await staff.evaluate(() => window.scrollBy(0, 600));
  await sleep(1000);
  await staff.screenshot({ path: `${OUT_DIR}/05-staff-order-garments.png`, fullPage: false });

  // 1-6: Scroll to photos & issues
  console.log('  📸 06 - Garment Photos & Issues');
  await staff.evaluate(() => window.scrollBy(0, 800));
  await sleep(1000);
  await staff.screenshot({ path: `${OUT_DIR}/06-staff-photos-issues.png`, fullPage: false });

  // 1-7: Continue scrolling to see QR code section
  console.log('  📸 07 - QR Code / Customer Confirm');
  await staff.evaluate(() => window.scrollBy(0, 1200));
  await sleep(1000);
  await staff.screenshot({ path: `${OUT_DIR}/07-staff-qr-section.png`, fullPage: false });

  // 1-8: Full page screenshot of order detail
  console.log('  📸 08 - Full Order Detail Page');
  await staff.evaluate(() => window.scrollTo(0, 0));
  await sleep(500);
  await staff.screenshot({ path: `${OUT_DIR}/08-staff-order-detail-full.png`, fullPage: true });

  // 1-9: New Order Page
  console.log('  📸 09 - New Order Page');
  await staff.goto(`${BASE_URL}/orders/new`);
  await sleep(2000);
  await staff.screenshot({ path: `${OUT_DIR}/09-staff-new-order.png`, fullPage: true });

  // 1-10: Receipt Page
  console.log('  📸 10 - Receipt Page');
  await staff.goto(`${BASE_URL}/orders/${order1Id}/receipt`);
  await sleep(2000);
  await staff.screenshot({ path: `${OUT_DIR}/10-staff-receipt.png`, fullPage: true });

  // 1-11: Inspection Report
  console.log('  📸 11 - Inspection Report');
  await staff.goto(`${BASE_URL}/orders/${order1Id}/report`);
  await sleep(2000);
  await staff.screenshot({ path: `${OUT_DIR}/11-staff-inspection-report.png`, fullPage: true });

  await staffCtx.close();

  // ═══════════════════════════════════════
  // PART 2: CUSTOMER SIGN — Mobile viewport
  // ═══════════════════════════════════════
  console.log('\n━━━ PART 2: Customer Confirmation ━━━');
  const custCtx = await browser.newContext({
    viewport: { width: 430, height: 932 },
    deviceScaleFactor: 2,
  });
  const cust = await custCtx.newPage();

  // Use Sarah's confirmation token
  const sarahToken = seedData.confirmations.sarah;
  console.log('  📸 12 - Customer Confirm Page (Top)');
  await cust.goto(`${BASE_URL}/sign/confirm/${sarahToken}`);
  await sleep(3000);
  await cust.screenshot({ path: `${OUT_DIR}/12-customer-confirm-top.png`, fullPage: false });

  // 2-2: Scroll to see garment photos
  console.log('  📸 13 - Customer Garment Photos');
  await cust.evaluate(() => window.scrollBy(0, 600));
  await sleep(1000);
  await cust.screenshot({ path: `${OUT_DIR}/13-customer-garment-photos.png`, fullPage: false });

  // 2-3: Scroll to see issues & signature area
  console.log('  📸 14 - Customer Issues & Signature');
  await cust.evaluate(() => window.scrollBy(0, 800));
  await sleep(1000);
  await cust.screenshot({ path: `${OUT_DIR}/14-customer-issues-signature.png`, fullPage: false });

  // 2-4: Full customer page
  console.log('  📸 15 - Full Customer Confirmation Page');
  await cust.evaluate(() => window.scrollTo(0, 0));
  await sleep(500);
  await cust.screenshot({ path: `${OUT_DIR}/15-customer-confirm-full.png`, fullPage: true });

  // Use Jennifer's token for a second confirmation view
  const jenToken = seedData.confirmations.jennifer;
  console.log('  📸 16 - Customer Confirm (Jennifer - Dress)');
  await cust.goto(`${BASE_URL}/sign/confirm/${jenToken}`);
  await sleep(3000);
  await cust.screenshot({ path: `${OUT_DIR}/16-customer-confirm-jennifer.png`, fullPage: true });

  await custCtx.close();

  // ═══════════════════════════════════════
  // PART 3: ADMIN DASHBOARD — Desktop viewport
  // ═══════════════════════════════════════
  console.log('\n━━━ PART 3: Admin Dashboard ━━━');
  const adminCtx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
  });
  const admin = await adminCtx.newPage();

  // 3-1: Admin Login Page
  console.log('  📸 17 - Admin Login');
  await admin.goto(`${BASE_URL}/admin/login`);
  await sleep(1500);
  await admin.screenshot({ path: `${OUT_DIR}/17-admin-login.png`, fullPage: false });

  // 3-2: Login
  await admin.fill('input[type="text"], input[name="username"], input[placeholder*="user" i], input:first-of-type', 'admin');
  await admin.fill('input[type="password"]', 'admin123');
  await admin.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign")');
  await sleep(2500);

  // 3-3: Dashboard
  console.log('  📸 18 - Admin Dashboard');
  await admin.screenshot({ path: `${OUT_DIR}/18-admin-dashboard.png`, fullPage: true });

  // 3-4: Orders Page
  console.log('  📸 19 - Admin Orders');
  await admin.goto(`${BASE_URL}/admin/orders`);
  await sleep(2000);
  await admin.screenshot({ path: `${OUT_DIR}/19-admin-orders.png`, fullPage: true });

  // 3-5: Order Detail
  console.log('  📸 20 - Admin Order Detail');
  await admin.goto(`${BASE_URL}/admin/orders/${order1Id}`);
  await sleep(2500);
  await admin.screenshot({ path: `${OUT_DIR}/20-admin-order-detail.png`, fullPage: true });

  // 3-6: Customers Page
  console.log('  📸 21 - Admin Customers');
  await admin.goto(`${BASE_URL}/admin/customers`);
  await sleep(2000);
  await admin.screenshot({ path: `${OUT_DIR}/21-admin-customers.png`, fullPage: true });

  // 3-7: Staff Page
  console.log('  📸 22 - Admin Staff Management');
  await admin.goto(`${BASE_URL}/admin/staff`);
  await sleep(2000);
  await admin.screenshot({ path: `${OUT_DIR}/22-admin-staff.png`, fullPage: true });

  await adminCtx.close();
  await browser.close();

  // ─── Summary ───
  const screenshots = fs.readdirSync(OUT_DIR).filter(f => f.endsWith('.png')).sort();
  console.log(`\n${'═'.repeat(50)}`);
  console.log(`✅ Captured ${screenshots.length} screenshots in ${OUT_DIR}`);
  console.log(`${'═'.repeat(50)}`);
  screenshots.forEach(f => {
    const stat = fs.statSync(path.join(OUT_DIR, f));
    console.log(`  ${f}  (${(stat.size / 1024).toFixed(0)} KB)`);
  });
})();
