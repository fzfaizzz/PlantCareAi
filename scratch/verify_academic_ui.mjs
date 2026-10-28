import { chromium } from '@playwright/test';

async function check() {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  // Go directly to detect page
  console.log('Navigating to http://127.0.0.1:8501/?page=Detect ...');
  await page.goto('http://127.0.0.1:8501/?page=Detect', { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForTimeout(2500);

  // Click sample leaf
  console.log('Selecting Spotted leaf sample...');
  const sampleBtn = page.locator('button:has-text("Spotted leaf")').first();
  await sampleBtn.click();
  await page.waitForTimeout(2000);

  // Now check radio options text
  const engineText = await page.locator('[data-testid="stRadio"]').innerText();
  console.log('\n=== ENGINE SELECTOR TEXT ===');
  console.log(engineText);

  // Click detect
  console.log('Clicking Detect Disease button...');
  const detectBtn = page.locator('button:has-text("Detect Disease")').first();
  await detectBtn.click();
  
  await page.locator('.st-key-analysis-result').waitFor({ state: 'visible', timeout: 45000 });
  await page.waitForTimeout(2000);

  // Check result text
  const badgeText = await page.locator('.engine-badge-banner').innerText();
  console.log('\n=== ENGINE BADGE TEXT ===');
  console.log(badgeText);

  const plantName = await page.locator('.result-summary-copy h2').innerText();
  const condition = await page.locator('.result-summary-copy h3').innerText();
  const scoreCaption = await page.locator('.confidence-caption').innerText();
  console.log('\n=== RESULT DETAILS ===');
  console.log({ plantName, condition, scoreCaption });

  // Check expanders
  const expanders = await page.locator('[data-testid="stExpander"]').allInnerTexts();
  console.log('\n=== EXPANDERS FOUND ===');
  expanders.forEach((exp, idx) => console.log(`[Expander ${idx+1}]:`, exp.split('\n')[0]));

  await page.screenshot({ path: 'qa/academic-sanitized-result.png', fullPage: true });
  console.log('\nSaved full page screenshot to qa/academic-sanitized-result.png');

  await browser.close();
}

check().catch(console.error);
