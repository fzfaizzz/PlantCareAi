import { chromium } from '@playwright/test';

async function verify() {
  console.log('=== VERIFYING NAVBAR & UPLOAD FIXES ===');
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto('http://127.0.0.1:8501', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // 1. Inspect Navbar Layout
  const navbarHtml = await page.locator('.st-key-navbar').innerHTML();
  console.log('\n[1] NAVBAR COLUMNS:');
  const cols = await page.locator('.st-key-navbar [data-testid="stColumn"]').all();
  console.log(`Found ${cols.length} column wrappers in navbar`);

  const brandText = await page.locator('.brand').innerText();
  console.log('Brand (Start):', brandText);

  const homeBtn = page.locator('button:has-text("Home")').first();
  const libBtn = page.locator('button:has-text("Plant Library")').first();
  const aboutBtn = page.locator('button:has-text("About")').first();

  console.log('Home button visible (Center):', await homeBtn.isVisible());
  console.log('Plant Library button visible (Center):', await libBtn.isVisible());
  console.log('About button visible (End):', await aboutBtn.isVisible());

  // Check About button classes / styling (should be primary green)
  const aboutClasses = await aboutBtn.getAttribute('class');
  const aboutTestId = await aboutBtn.getAttribute('data-testid');
  console.log(`About button testId="${aboutTestId}", class="${aboutClasses}"`);

  // 2. Inspect Dropzone Button Count and Text Before File Upload
  console.log('\n[2] DROPZONE BUTTONS (BEFORE UPLOAD):');
  const initialButtons = await page.locator('.st-key-leaf-upload button').all();
  console.log('Number of buttons inside leaf-upload:', initialButtons.length);

  // 3. Upload a file and verify button count & styling
  console.log('\n[3] UPLOADING A FILE INTO DROPZONE:');
  const fileInput = page.locator('input[type="file"]').first();
  await fileInput.setInputFiles('public/assets/plants/sample-leaf-spotted.webp');
  await page.waitForTimeout(3000);

  // Check how many visible buttons exist inside leaf-upload
  const visibleUploadButtons = await page.locator('.st-key-leaf-upload button:visible').all();
  console.log('Number of VISIBLE buttons inside leaf-upload after upload (must be <= 1):', visibleUploadButtons.length);

  // Take full screenshot of page
  await page.screenshot({ path: 'qa/navbar-and-uploader-verified.png', fullPage: true });
  console.log('\nSaved qa/navbar-and-uploader-verified.png');

  await browser.close();
  console.log('=== VERIFICATION COMPLETED ===');
}

verify().catch(console.error);
