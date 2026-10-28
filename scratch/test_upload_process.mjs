import { chromium } from '@playwright/test';

async function testUploadProcess() {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://127.0.0.1:8501', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // Upload file
  console.log('Uploading sample file...');
  const fileInput = page.locator('input[type="file"]').first();
  await fileInput.setInputFiles('public/assets/plants/sample-leaf-spotted.webp');
  await page.waitForTimeout(3000);

  // Take screenshot of dropzone area
  await page.screenshot({ path: 'qa/after-file-input.png' });

  // Check what buttons exist
  const buttons = await page.locator('[data-testid="stFileUploader"] button').all();
  console.log('Buttons inside stFileUploader:', buttons.length);
  for (let i = 0; i < buttons.length; i++) {
    const text = await buttons[i].innerText();
    const html = await buttons[i].evaluate(el => el.outerHTML);
    console.log(`\nButton ${i+1}: innerText="${text}"`);
    console.log(`HTML: ${html}`);
  }

  // Check if preview is rendered below
  const hasDetectBtn = await page.locator('button:has-text("Detect Disease")').count();
  console.log('Has Detect Disease button:', hasDetectBtn > 0);

  await browser.close();
}

testUploadProcess().catch(console.error);
