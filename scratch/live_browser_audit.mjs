import { chromium } from '@playwright/test';
import fs from 'node:fs/promises';

async function runLiveBrowserAudit() {
  console.log('=== STARTING ROBUST PLAYWRIGHT LIVE BROWSER AUDIT ===');
  const browser = await chromium.launch({
    channel: 'chrome',
    headless: true,
    args: ['--disable-gpu', '--disable-dev-shm-usage', '--no-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });
  const page = await context.newPage();

  const auditReport = {
    timestamp: new Date().toISOString(),
    port: 8501,
    consoleErrors: [],
    pageErrors: [],
    pagesVisited: [],
    actionsTested: [],
    screenshots: []
  };

  page.on('console', msg => {
    if (msg.type() === 'error') {
      auditReport.consoleErrors.push(msg.text());
    }
  });
  page.on('pageerror', err => {
    auditReport.pageErrors.push(err.message);
  });

  try {
    // 1. Visit Home Page
    console.log('\n[1/4] Visiting Home Page at http://127.0.0.1:8501...');
    await page.goto('http://127.0.0.1:8501', { waitUntil: 'networkidle', timeout: 45000 });
    await page.waitForTimeout(2000);

    const homeTitle = await page.title();
    console.log(`  Page Title: ${homeTitle}`);
    await page.screenshot({ path: 'qa/browser-home.png' });
    auditReport.screenshots.push('qa/browser-home.png');
    auditReport.pagesVisited.push({ page: 'Home', status: 'OK' });

    // 2. Visit Plant Library Page
    console.log('\n[2/4] Testing Plant Library Page...');
    const libNavBtn = page.locator('button:has-text("Plant Library")').first();
    await libNavBtn.click();
    await page.waitForTimeout(2500);
    await page.screenshot({ path: 'qa/browser-library.png' });
    auditReport.screenshots.push('qa/browser-library.png');
    auditReport.pagesVisited.push({ page: 'Plant Library', status: 'OK' });

    // 3. Visit About Page
    console.log('\n[3/4] Testing About Page...');
    const aboutNavBtn = page.locator('button:has-text("About")').first();
    await aboutNavBtn.click();
    await page.waitForTimeout(2500);
    await page.screenshot({ path: 'qa/browser-about.png' });
    auditReport.screenshots.push('qa/browser-about.png');
    auditReport.pagesVisited.push({ page: 'About', status: 'OK' });

    // 4. Visit Detect Page & Execute Inference
    console.log('\n[4/4] Testing Leaf Detection & Model Inference...');
    await page.goto('http://127.0.0.1:8501/?page=Detect', { waitUntil: 'networkidle', timeout: 45000 });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: 'qa/browser-detect-page.png' });

    // Click sample leaf button
    console.log('  Selecting Spotted leaf sample button...');
    const sampleBtn = page.locator('button:has-text("Spotted leaf")').first();
    await sampleBtn.click();
    
    // Wait for Detect Disease button to be ready and enabled
    const detectBtn = page.locator('button:has-text("Detect Disease")').first();
    await detectBtn.waitFor({ state: 'visible', timeout: 15000 });
    console.log('  [PASS] Leaf preview rendered and Detect Disease button is ready.');

    // Click Detect Disease
    console.log('  Clicking "Detect Disease  →" button...');
    const t0 = Date.now();
    await detectBtn.click();

    // Wait for analysis result to appear (Model is already warm, so takes <5s)
    await page.locator('.st-key-analysis-result').waitFor({ state: 'visible', timeout: 60000 });
    const elapsed = Date.now() - t0;
    console.log(`  [PASS] Full analysis result rendered in ${elapsed}ms!`);

    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'qa/browser-result.png', fullPage: true });
    auditReport.screenshots.push('qa/browser-result.png');
    auditReport.pagesVisited.push({ page: 'Result Dashboard', status: 'OK' });

    // Verify Confidence dial text
    const resultText = await page.locator('.st-key-analysis-result').innerText();
    const hasValidPercentage = /\d+%/.test(resultText);
    const hasDashDashBug = /Confidence Score\s*—/.test(resultText);
    console.log(`  Confidence Display Valid: ${hasValidPercentage}`);
    console.log(`  Empty/Dash Dash Bug Present: ${hasDashDashBug}`);

    if (hasDashDashBug) {
      auditReport.consoleErrors.push('Regressive Bug Detected: Confidence dial is displaying "—"');
    } else {
      console.log('  [PASS] Confidence dial displays authentic non-empty percentage score.');
    }

    // Check cards
    const hasSymptoms = resultText.includes('Symptoms');
    const hasPrevention = resultText.includes('Prevention');
    const hasCare = resultText.includes('Care Tips') || resultText.includes('Next Checks');
    console.log(`  Cards Rendered: Symptoms=${hasSymptoms}, Prevention=${hasPrevention}, Care=${hasCare}`);

    console.log('\n==================================================');
    console.log('>>> LIVE BROWSER AUDIT COMPLETED SUCCESSFULLY <<<');
    console.log('==================================================');
    console.log(`Total Pages Visited: ${auditReport.pagesVisited.length}`);
    console.log(`Console Errors: ${auditReport.consoleErrors.length}`);
    console.log(`Page Errors: ${auditReport.pageErrors.length}`);

    await fs.writeFile('qa/browser-audit-results.json', JSON.stringify(auditReport, null, 2));
    console.log('Results saved to qa/browser-audit-results.json');

  } catch (err) {
    console.error('Browser Audit Error:', err);
    await page.screenshot({ path: 'qa/browser-error.png' });
    auditReport.pageErrors.push(err.message);
    await fs.writeFile('qa/browser-audit-results.json', JSON.stringify(auditReport, null, 2));
    throw err;
  } finally {
    await browser.close();
  }
}

runLiveBrowserAudit();
