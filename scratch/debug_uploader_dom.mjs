import { chromium } from '@playwright/test';

async function debugUpload() {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://127.0.0.1:8501/?page=Detect', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);

  // Set file directly into file uploader input
  const fileInput = await page.locator('input[type="file"]').first();
  await fileInput.setInputFiles('public/assets/plants/sample-leaf-spotted.webp');
  await page.waitForTimeout(3000);

  // Grab all buttons inside stFileUploader
  const buttons = await page.locator('[data-testid="stFileUploader"] button').all();
  console.log(`Found ${buttons.length} buttons inside stFileUploader!`);
  for (let i = 0; i < buttons.length; i++) {
    const text = await buttons[i].innerText();
    const html = await buttons[i].evaluate(el => el.outerHTML);
    console.log(`\n--- Button ${i+1} ---`);
    console.log(`Text: "${text}"`);
    console.log(`HTML: ${html}`);
  }

  // Also check all elements inside stFileUploader
  const uploaderHtml = await page.locator('[data-testid="stFileUploader"]').evaluate(el => el.innerHTML);
  console.log('\n--- Entire stFileUploader innerHTML ---\n', uploaderHtml);

  await page.screenshot({ path: 'qa/file-uploader-debug.png' });
  console.log('\nScreenshot saved to qa/file-uploader-debug.png');

  await browser.close();
}

debugUpload().catch(console.error);
