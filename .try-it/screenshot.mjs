import { chromium } from 'playwright';

const BASE = 'http://localhost:3100';
const OIDC = 'http://localhost:10090';
const SCREENSHOT_DIR = '.try-it/screenshots';

async function getToken(browser, loginHint) {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  // Follow OIDC flow
  const authUrl = `${OIDC}/authorize?client_id=mock-oidc-client&response_type=code&scope=openid+email+profile&redirect_uri=${encodeURIComponent(BASE + '/api/auth/callback')}&login_hint=${loginHint}`;
  await page.goto(authUrl, { waitUntil: 'networkidle', timeout: 15000 });
  // After callback, we should be on /dashboard
  await page.waitForTimeout(2000);
  const cookies = await ctx.cookies();
  const token = cookies.find(c => c.name === 'token');
  return { ctx, page, token: token?.value };
}

async function screenshotPages(browser, role, loginHint, pages) {
  const { ctx, page } = await getToken(browser, loginHint);
  
  for (const [name, path] of pages) {
    try {
      await page.goto(`${BASE}${path}`, { waitUntil: 'networkidle', timeout: 15000 });
      await page.waitForTimeout(1500);
      await page.screenshot({ path: `${SCREENSHOT_DIR}/${role}_${name}.png`, fullPage: false });
      console.log(`  ${role}/${name}: OK`);
    } catch (e) {
      console.log(`  ${role}/${name}: FAILED (${e.message.slice(0, 60)})`);
    }
  }
  await ctx.close();
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  
  // Screenshot login page (unauthenticated)
  const loginCtx = await browser.newContext();
  const loginPage = await loginCtx.newPage();
  await loginPage.goto(BASE, { waitUntil: 'networkidle', timeout: 15000 });
  await loginPage.waitForTimeout(1500);
  await loginPage.screenshot({ path: `${SCREENSHOT_DIR}/login_page.png`, fullPage: false });
  console.log('  login_page: OK');
  await loginCtx.close();

  // Admin pages
  console.log('Admin (Super Admin):');
  await screenshotPages(browser, 'admin', 'mock-admin', [
    ['dashboard', '/dashboard'],
    ['rfcs', '/rfcs'],
    ['rfc_detail', '/rfcs/20000000-0000-0000-0000-000000000001'],
    ['rfc_new', '/rfcs/new'],
    ['reviews', '/reviews'],
    ['admin_users', '/admin/users'],
    ['admin_roles', '/admin/roles'],
    ['admin_settings', '/admin/settings'],
  ]);

  // Manager pages
  console.log('Manager:');
  await screenshotPages(browser, 'manager', 'mock-manager', [
    ['dashboard', '/dashboard'],
    ['rfcs', '/rfcs'],
    ['reviews', '/reviews'],
  ]);

  // User pages
  console.log('User:');
  await screenshotPages(browser, 'user', 'mock-user', [
    ['dashboard', '/dashboard'],
    ['rfcs', '/rfcs'],
    ['reviews', '/reviews'],
  ]);

  await browser.close();
  console.log('Done!');
})();
