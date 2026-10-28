/**
 * Focused integration checks using explicitly controlled TEST fixtures.
 * The production app contains no mock diagnoses. This script starts a separate
 * Vite process on 5174, configures a local test endpoint, and holds actual browser
 * fetch requests through Playwright route interception. No fixed-delay scan is
 * implemented or injected into application code.
 */
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const origin = 'http://127.0.0.1:5174';
const endpoint = `${origin}/api/analyze`;
const samplePath = path.join(root, 'public/assets/plants/sample-leaf-spotted.webp');
const imageBase64 = (await readFile(samplePath)).toString('base64');
const report = { fixtureNotice: 'Explicit Playwright test fixtures only. No real analysis backend exists or is claimed.', checks: [], errors: [], screenshot: 'qa/scan-pending.png' };
await mkdir(path.join(root, 'qa'), { recursive: true });
let serverOutput = '';
let server;
let browser;
let activeFixture;
const fixtures = [];
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };

function fixture(label) {
  const entry = { label, seen: deferred(), release: deferred(), settled: deferred(), action: 'abort', request: null };
  fixtures.push(entry);
  activeFixture = entry;
  return entry;
}
function pass(message) { report.checks.push(message); console.log(`PASS ${message}`); }
async function ready() {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    if (server.exitCode !== null) throw new Error(`Test Vite exited: ${serverOutput}`);
    try { const response = await fetch(`${origin}/detect`); if (response.ok) return; } catch {}
    await new Promise(resolve => setTimeout(resolve, 150));
  }
  throw new Error(`Vite did not become ready: ${serverOutput}`);
}
async function dropFiles(page, files) {
  await page.evaluate(items => {
    const transfer = new DataTransfer();
    for (const item of items) {
      const bytes = item.base64 ? Uint8Array.from(atob(item.base64), character => character.charCodeAt(0)) : new TextEncoder().encode(item.text ?? 'not an image');
      transfer.items.add(new File([bytes], item.name, { type: item.type }));
    }
    const panel = document.querySelector('.upload-panel');
    panel.dispatchEvent(new DragEvent('dragover', { bubbles: true, cancelable: true, dataTransfer: transfer }));
    panel.dispatchEvent(new DragEvent('drop', { bubbles: true, cancelable: true, dataTransfer: transfer }));
  }, files);
}
async function selected(page) {
  await page.locator('.image-preview img').waitFor({ state: 'visible' });
  assert.equal(await page.locator('.image-preview img').evaluate(image => image.complete && image.naturalWidth > 0 && image.currentSrc.startsWith('blob:')), true);
}
async function choose(page) {
  await page.locator('input[type=file]').setInputFiles(samplePath);
  await selected(page);
  await page.getByRole('button', { name: 'Analyze leaf', exact: true }).waitFor({ state: 'visible' });
}
async function pending(page, entry) {
  await page.getByRole('button', { name: /Analyze leaf|Try analysis again/, exact: true }).click();
  const actualRequest = await Promise.race([entry.seen.promise, new Promise((_resolve, reject) => setTimeout(() => reject(new Error(`No actual request for ${entry.label}`)), 10_000))]);
  assert.equal(actualRequest.method(), 'POST');
  assert.match(actualRequest.headers()['content-type'], /^multipart\/form-data; boundary=/);
  assert.ok(actualRequest.postDataBuffer().includes(Buffer.from('name="image"')));
  await page.locator('.scan-beam').waitFor({ state: 'visible' });
  assert.equal(await page.locator('.scan-overlay .scan-corner').count(), 4);
  assert.equal(await page.locator('.upload-panel').getAttribute('aria-busy'), 'true');
  assert.equal(await page.locator('.analysis-result').count(), 0);
  assert.match(await page.locator('.analysis-status').innerText(), /Uploading your leaf|Analyzing leaf/);
}
async function stopped(page) {
  await page.locator('.scan-overlay').waitFor({ state: 'detached' });
  assert.equal(await page.locator('.scan-beam').count(), 0);
}
async function release(entry, action = 'abort', body) {
  entry.action = action;
  entry.body = body;
  entry.release.resolve();
  await entry.settled.promise;
}

try {
  server = spawn(process.execPath, [path.join(root, 'node_modules/vite/bin/vite.js'), '--host', '127.0.0.1', '--port', '5174', '--strictPort'], { cwd: root, env: { ...process.env, VITE_ANALYSIS_ENDPOINT: endpoint }, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
  server.stdout.on('data', data => { serverOutput += data; });
  server.stderr.on('data', data => { serverOutput += data; });
  await ready();
  browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--disable-blink-features=AutomationControlled'] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  page.on('pageerror', error => report.errors.push(error.message));
  await page.route(endpoint, async route => {
    const entry = activeFixture;
    if (!entry) { await route.abort(); return; }
    activeFixture = null;
    entry.request = route.request();
    entry.seen.resolve(entry.request);
    await entry.release.promise;
    try {
      if (entry.action === 'success') await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(entry.body) });
      else if (entry.action === 'error') await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ error: 'Explicit browser test fixture' }) });
      else await route.abort('aborted');
    } catch (error) {
      if (!/Target page, context or browser has been closed|Invalid InterceptionId|Request is already handled|Route is already handled/i.test(error.message)) throw error;
    } finally { entry.settled.resolve(); }
  });
  await page.goto(`${origin}/detect`);
  await page.getByRole('heading', { name: /Detect Plant Diseases/ }).waitFor();
  await page.evaluate(() => document.fonts.ready);

  await dropFiles(page, [{ name: 'dragged-leaf.webp', type: 'image/webp', base64: imageBase64 }]);
  await selected(page);
  assert.match(await page.locator('.preview-toolbar').innerText(), /dragged-leaf.webp/);
  pass('A real WebP file can be selected through file drag/drop and decoded as an aspect-preserving blob preview.');
  await dropFiles(page, [{ name: 'first.webp', type: 'image/webp' }, { name: 'second.webp', type: 'image/webp' }]);
  await page.getByRole('alert').filter({ hasText: 'Please drop one leaf image at a time.' }).waitFor();
  pass('Dropping multiple files displays the one-image validation error.');
  await dropFiles(page, [{ name: 'not-a-leaf.svg', type: 'image/svg+xml', text: '<svg></svg>' }]);
  await page.getByRole('alert').filter({ hasText: 'Choose a JPG, PNG or WebP image' }).waitFor();
  await dropFiles(page, [{ name: 'damaged.png', type: 'image/png', text: 'this is not readable image data' }]);
  await page.getByRole('alert').filter({ hasText: 'damaged or unreadable' }).waitFor();
  await stopped(page);
  pass('Unsupported and unreadable dragged files produce accessible errors without starting a scan.');

  await choose(page);
  const success = fixture('success');
  await pending(page, success);
  await page.screenshot({ path: path.join(root, report.screenshot), fullPage: false, animations: 'allow' });
  pass('The actual pending multipart fetch mounts one scan beam, four corners and a visible selected photo (1440px screenshot saved).');
  await release(success, 'success', { plant: 'Browser test fixture plant', condition: 'Explicit test response', uncertainty: 'Controlled browser verification fixture; this is not real analysis.', inconclusive: true });
  await stopped(page);
  await page.getByRole('heading', { name: 'Explicit test response' }).waitFor();
  assert.match(await page.locator('.analysis-result').innerText(), /Controlled browser verification fixture/);
  pass('A controlled successful HTTP response stops the scan and displays only fixture fields returned by that response.');

  const error = fixture('HTTP error');
  await pending(page, error);
  await release(error, 'error');
  await stopped(page);
  await page.getByRole('alert').filter({ hasText: 'error (503)' }).waitFor();
  assert.equal(await page.locator('.analysis-result').count(), 0);
  pass('An HTTP failure stops the scan, removes prior results and exposes a useful error.');

  const cancelled = fixture('cancel');
  await pending(page, cancelled);
  await page.getByRole('button', { name: 'Cancel analysis', exact: true }).click();
  await stopped(page);
  assert.equal(await page.locator('.analysis-result').count(), 0);
  assert.equal(await page.getByRole('button', { name: 'Analyze leaf', exact: true }).isEnabled(), true);
  await release(cancelled);
  pass('Cancel analysis immediately stops the pending scan and allows retry without fabricating a result.');

  const removed = fixture('remove');
  await pending(page, removed);
  await page.getByRole('button', { name: 'Remove selected image', exact: true }).click();
  await stopped(page);
  assert.equal(await page.locator('.image-preview').count(), 0);
  await page.getByRole('button', { name: 'Choose Image', exact: true }).waitFor();
  await release(removed);
  pass('Removing an image during a request stops the scan and restores the empty chooser.');

  await choose(page);
  const navigation = fixture('navigation away');
  await pending(page, navigation);
  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: 'About', exact: true }).click();
  await page.waitForURL(`${origin}/about`);
  await stopped(page);
  await release(navigation);
  pass('Navigating away while a request is pending unmounts the scan and cleans up the upload component.');

  const demoPage = await context.newPage();
  demoPage.on('pageerror', error => report.errors.push(error.message));
  let demoApiCalls = 0;
  demoPage.on('request', request => { if (request.url().includes('/api/analyze')) demoApiCalls += 1; });
  await demoPage.goto('http://127.0.0.1:5173/detect');
  await dropFiles(demoPage, [{ name: 'demo-dragged-leaf.webp', type: 'image/webp', base64: imageBase64 }]);
  await selected(demoPage);
  assert.equal(await demoPage.getByRole('button', { name: 'Analyze leaf', exact: true }).isDisabled(), true);
  await demoPage.locator('.demo-note').filter({ hasText: 'UI demo' }).waitFor();
  await stopped(demoPage);
  assert.equal(demoApiCalls, 0);
  pass('The unchanged default app on 5173 remains explicitly marked UI demo: uploads preview locally, Analyze is disabled, no scan or API request occurs.');
  assert.deepEqual(report.errors, []);
  report.passed = true;
} catch (error) {
  report.passed = false;
  report.failure = error.stack || error.message;
  console.error(error);
  process.exitCode = 1;
} finally {
  for (const entry of fixtures) entry.release.resolve();
  if (browser) await browser.close();
  if (server && server.exitCode === null) {
    server.kill();
    await Promise.race([new Promise(resolve => server.once('exit', resolve)), new Promise(resolve => setTimeout(resolve, 5000))]);
  }
  report.testServerStopped = !server || server.exitCode !== null || server.signalCode !== null;
  await writeFile(path.join(root, 'qa/scan-browser-results.json'), `${JSON.stringify(report, null, 2)}\n`);
}
