import { chromium } from '@playwright/test';

async function logElements() {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://127.0.0.1:8501', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  const fileInputs = await page.locator('input[type="file"]').count();
  console.log('File inputs on http://127.0.0.1:8501:', fileInputs);

  const uploaderCount = await page.locator('[data-testid="stFileUploader"]').count();
  console.log('stFileUploader count:', uploaderCount);

  const testIds = await page.locator('[data-testid]').evaluateAll(els => els.map(e => e.getAttribute('data-testid')));
  console.log('TestIDs found:', [...new Set(testIds)].filter(t => t.toLowerCase().includes('upload')));

  await page.screenshot({ path: 'qa/clean-home.png' });
  await browser.close();
}

logElements().catch(console.error);
