import { chromium } from '@playwright/test';

async function verifyAll() {
  console.log('=== VERIFYING ALL USER REQUESTED UI EDITS ===');
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // 1. Check Navbar on Home Page
  await page.goto('http://127.0.0.1:8501', { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForTimeout(2000);
  const navbarText = await page.locator('.st-key-navbar').innerText();
  console.log('\n[1] NAVBAR TEXT:\n', navbarText);
  const hasLogin = navbarText.includes('Log in') || navbarText.includes('Sign up');
  console.log('  -> Are "Log in" or "Sign up" present?:', hasLogin ? 'YES (FAIL)' : 'NO (PASSED - CLEAN)');

  // 2. Check Detect Page before selecting any image
  await page.goto('http://127.0.0.1:8501/?page=Detect', { waitUntil: 'networkidle', timeout: 45000 });
  await page.waitForTimeout(2000);
  const dropzoneVisible = await page.locator('.st-key-leaf-upload').isVisible();
  console.log('\n[2] DETECT PAGE DROPZONE:');
  console.log('  -> Is dropzone container visible?:', dropzoneVisible);
  await page.screenshot({ path: 'qa/verify-detect-dropzone.png' });

  // 3. Select sample leaf
  console.log('\n[3] SELECTING SAMPLE LEAF:');
  const sampleBtn = page.locator('button:has-text("Spotted leaf")').first();
  await sampleBtn.click();
  await page.waitForTimeout(2000);

  // Check if dropzone disappeared and preview took over cleanly
  const dropzoneAfterSelect = await page.locator('.st-key-leaf-upload').count();
  console.log('  -> Dropzone count after selecting image (should be 0):', dropzoneAfterSelect);
  const detectBtnVisible = await page.locator('button:has-text("Detect Disease")').first().isVisible();
  console.log('  -> Is "Detect Disease" button visible?:', detectBtnVisible);
  await page.screenshot({ path: 'qa/verify-detect-selected.png' });

  // 4. Click Detect Disease and verify Result Screen
  console.log('\n[4] RUNNING DETECTION:');
  await page.locator('button:has-text("Detect Disease")').first().click();
  await page.locator('.st-key-analysis-result').waitFor({ state: 'visible', timeout: 45000 });
  await page.waitForTimeout(2000);

  // Check top model banner
  const bannerCount = await page.locator('.engine-badge-banner').count();
  console.log('  -> Top Model Name Banner count (should be 0):', bannerCount);

  // Check thumbnails under photo
  const thumbsCount = await page.locator('.st-key-result-thumbs').count();
  console.log('  -> Thumbnails under photo count (should be 0):', thumbsCount);

  // Check left actions under photo
  const leftActionsText = await page.locator('.st-key-result-actions').innerText();
  console.log('  -> Actions under photo text:\n', leftActionsText);
  const hasAnother = leftActionsText.includes('Analyse Another Leaf');
  const hasDownload = leftActionsText.includes('Download Result');
  const hasShare = leftActionsText.includes('Share Result');
  console.log('  -> "Analyse Another Leaf" present under photo?:', hasAnother);
  console.log('  -> "Download Result" present under photo?:', hasDownload);
  console.log('  -> "Share Result" present anywhere (should be false)?:', hasShare);

  await page.screenshot({ path: 'qa/verify-result-final.png', fullPage: true });
  console.log('\nFull result screenshot saved to qa/verify-result-final.png');

  await browser.close();
  console.log('\n=== ALL CHECKS COMPLETED ===');
}

verifyAll().catch(console.error);
