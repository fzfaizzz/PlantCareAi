import { chromium } from '@playwright/test';

async function check() {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  await page.goto('http://127.0.0.1:8501/?page=Detect', { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForTimeout(2500);

  // Click sample leaf
  const sampleBtn = page.locator('button:has-text("Spotted leaf")').first();
  await sampleBtn.click();
  await page.waitForTimeout(2000);

  // Print all radio/radiogroup text
  const radios = await page.locator('role=radiogroup').allInnerTexts();
  console.log('RADIOGROUPS:', radios);

  // Click detect
  const detectBtn = page.locator('button:has-text("Detect Disease")').first();
  await detectBtn.click();
  
  await page.locator('.st-key-analysis-result').waitFor({ state: 'visible', timeout: 45000 });
  await page.waitForTimeout(2000);

  // Grab all innerText of analysis-result
  const text = await page.locator('.st-key-analysis-result').innerText();
  console.log('=== ANALYSIS RESULT RENDERED TEXT ===\n', text);

  // Search specifically for any occurrence of "gemini" in the page text
  const fullBody = await page.locator('body').innerText();
  const hasGemini = fullBody.toLowerCase().includes('gemini');
  console.log('\nDoes the UI contain "Gemini"?:', hasGemini ? 'YES (BUG)' : 'NO (100% SANITIZED & CLEAN)');

  await page.screenshot({ path: 'qa/academic-sanitized-result.png', fullPage: true });
  console.log('Saved screenshot to qa/academic-sanitized-result.png');

  await browser.close();
}

check().catch(console.error);
