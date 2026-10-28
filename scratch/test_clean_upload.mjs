import { chromium } from '@playwright/test';

async function testCleanUpload() {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  // New incognito context
  const context = await browser.newContext();
  const page = await context.newPage({ viewport: { width: 1440, height: 900 } });
  
  await page.goto('http://127.0.0.1:8501/?page=Detect', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // Find file input
  const fileInput = page.locator('input[type="file"]').first();
  const exists = await fileInput.count();
  console.log('File input count on fresh page:', exists);

  if (exists > 0) {
    // Upload sample file
    console.log('Uploading sample leaf image...');
    await fileInput.setInputFiles('public/assets/plants/sample-leaf-spotted.webp');
    await page.waitForTimeout(3000);

    // Get all buttons inside stFileUploader
    const btns = await page.locator('[data-testid="stFileUploader"] button').all();
    console.log('Buttons found after upload:', btns.length);
    for (let i = 0; i < btns.length; i++) {
      const ariaLabel = await btns[i].getAttribute('aria-label');
      const testId = await btns[i].getAttribute('data-testid');
      const className = await btns[i].getAttribute('class');
      const innerText = await btns[i].innerText();
      console.log(`Btn ${i+1}: aria-label="${ariaLabel}", testId="${testId}", class="${className}", innerText="${innerText}"`);
    }

    await page.screenshot({ path: 'qa/fresh-upload-test.png' });
    console.log('Saved qa/fresh-upload-test.png');
  }

  await browser.close();
}

testCleanUpload().catch(console.error);
