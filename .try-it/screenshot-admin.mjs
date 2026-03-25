import { chromium } from 'playwright';

const BASE = 'http://localhost:3100';
const OIDC = 'http://localhost:10090';
const DIR = '.try-it/screenshots';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  
  // Login as admin
  const authUrl = `${OIDC}/authorize?client_id=mock-oidc-client&response_type=code&scope=openid+email+profile&redirect_uri=${encodeURIComponent(BASE + '/api/auth/callback')}&login_hint=mock-admin`;
  await page.goto(authUrl, { waitUntil: 'load', timeout: 30000 });
  await page.waitForTimeout(3000);
  
  for (const [name, path] of [['admin_users', '/admin/users'], ['admin_roles', '/admin/roles'], ['admin_settings', '/admin/settings']]) {
    try {
      await page.goto(`${BASE}${path}`, { waitUntil: 'load', timeout: 30000 });
      await page.waitForTimeout(3000);
      await page.screenshot({ path: `${DIR}/admin_${name}.png`, fullPage: false });
      console.log(`${name}: OK`);
    } catch (e) {
      console.log(`${name}: FAILED - ${e.message.slice(0, 80)}`);
    }
  }
  
  await browser.close();
})();
