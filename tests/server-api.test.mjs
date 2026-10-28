import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import sharp from 'sharp';
import { createApiHandler } from '../server/index.mjs';
import { ApiError } from '../server/errors.mjs';
import { validateAnalysisResponse } from '../src/lib/analysis.mjs';

const env = { GEMINI_API_KEY: 'TEST-ONLY-NOT-A-REAL-KEY', GEMINI_MODEL: 'test-only-gemini-model', RATE_LIMIT_PER_MINUTE: '120' };
const standardAssessment = {
  contains_leaf: 'yes', image_quality: 'usable',
  plant: { common_name: 'Tomato', scientific_name: 'Solanum lycopersicum' },
  possible_condition: 'Early Blight', visible_symptoms: ['Brown leaf spots'], limitations: ['One photo cannot confirm the cause.'],
};
const mock = assessment => ({ assess: async () => assessment || structuredClone(standardAssessment) });

async function fixture(format = 'jpeg', width = 128, height = 128) {
  const raw = Buffer.alloc(width * height * 3);
  for (let i = 0; i < raw.length; i++) raw[i] = (i * 17 + Math.floor(i / 31)) % 255;
  return sharp(raw, { raw: { width, height, channels: 3 } }).toFormat(format).toBuffer();
}

async function withServer(options, run) {
  const handler = createApiHandler({ env, logger: {}, ...options });
  const server = http.createServer(handler);
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = 'http://127.0.0.1:' + server.address().port;
  try { await run(base); } finally {
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
  }
}

function upload(base, image, name = 'leaf.jpg', extra = {}) {
  const form = new FormData();
  form.append('image', new Blob([image], { type: 'image/jpeg' }), name);
  return fetch(base + '/api/analyze', { method: 'POST', body: form, ...extra });
}

test('health is honest, key stays private, no TensorFlow classifier is advertised', async () => {
  await withServer({ env: {} }, async base => {
    const health = await fetch(base + '/api/health');
    assert.equal(health.status, 200);
    const body = await health.json();
    assert.equal(body.provider.configured, false);
    assert.equal(body.provider.live_verified, false);
    assert.equal(body.limits.quota_scope, 'per_instance');
    const info = await (await fetch(base + '/api/model-info')).json();
    assert.equal(info.tensorflow_enabled, false);
    assert.equal(info.trained_classifier, false);
    const missing = await upload(base, await fixture());
    assert.equal(missing.status, 503);
    assert.equal((await missing.json()).code, 'analysis_unavailable');
  });
});

test('actual multipart decode yields v2 contract with no invented score', async () => {
  let calls = 0;
  const client = { assess: async image => {
    calls++;
    const metadata = await sharp(image).metadata();
    assert.equal(metadata.format, 'jpeg');
    assert.equal(metadata.exif, undefined);
    return standardAssessment;
  } };
  await withServer({ geminiClient: client }, async base => {
    const response = await upload(base, await fixture());
    assert.equal(response.status, 200);
    const body = await response.json();
    assert.equal(body.schema_version, '2.0');
    assert.equal(validateAnalysisResponse(body).schema_version, '2.0');
    assert.equal(body.status, 'success');
    assert.equal(body.confidence, null);
    assert.equal(body.catalog.plant_village_class, 'Tomato___Early_blight');
    assert.equal(body.provider.name, 'gemini');
    assert.equal(body.provider.model, env.GEMINI_MODEL);
    assert.equal(body.model, undefined);
    assert.equal(body.top_predictions, undefined);
    assert.deepEqual(body.observations, ['Brown leaf spots']);
    assert.equal(body.request_id, response.headers.get('x-request-id'));
    assert.ok(body.sources.every(source => source.url.startsWith('https://')));
    assert.ok(body.timings_ms.total >= 0);
    assert.equal(calls, 1);
    assert.ok(!JSON.stringify(body).includes(env.GEMINI_API_KEY));
  });
});

test('unknown plant or unmatched condition stays uncertain and receives general guidance only', async () => {
  const assessment = { ...standardAssessment, plant: { common_name: 'Neem', scientific_name: 'Azadirachta indica' }, possible_condition: 'Unknown leaf damage' };
  await withServer({ geminiClient: mock(assessment) }, async base => {
    const body = await (await upload(base, await fixture())).json();
    assert.equal(body.status, 'uncertain');
    assert.equal(body.plant, 'Neem');
    assert.equal(validateAnalysisResponse(body).status, 'uncertain');
    assert.deepEqual(body.care, []);
    assert.deepEqual(body.prevention, []);
    assert.equal(body.general_guidance.length, 2);
    assert.ok(body.general_guidance_source.url.startsWith('https://apps.extension.umn.edu/'));
    assert.equal(body.catalog.matched, false);
    assert.equal(body.catalog.plant_village_class, null);
    assert.ok(body.sources[0].attribution.includes('General'));
    assert.ok(!body.care.some(text => /fungicide|pesticide/i.test(text)));
  });
});

test('non-leaf and poor quality are not green disease results', async () => {
  await withServer({ geminiClient: mock({ ...standardAssessment, contains_leaf: 'no', plant: null, possible_condition: null }) }, async base => {
    const body = await (await upload(base, await fixture())).json();
    assert.equal(body.status, 'unsupported_image');
    assert.equal(body.plant, null);
    assert.equal(body.condition, null);
    assert.deepEqual(body.care, []);
  });
  await withServer({ geminiClient: mock({ ...standardAssessment, image_quality: 'poor' }) }, async base => {
    assert.equal((await (await upload(base, await fixture())).json()).status, 'uncertain');
  });
});

test('empty, corrupt, disguised, tiny, and unsupported uploads never call Gemini', async () => {
  let calls = 0;
  await withServer({ geminiClient: { assess: async () => { calls++; return standardAssessment; } } }, async base => {
    const empty = await upload(base, Buffer.alloc(0));
    assert.equal(empty.status, 422);
    const text = await upload(base, Buffer.from('not an image'), 'leaf.jpg');
    assert.equal(text.status, 415);
    const corrupt = await upload(base, Buffer.from([0xff, 0xd8, 0xff, 0xe0, 0, 1, 3]));
    assert.equal(corrupt.status, 422);
    const tiny = await upload(base, await fixture('png', 16, 16));
    assert.equal(tiny.status, 422);
    const svg = await upload(base, Buffer.from('<svg width="80" height="80"></svg>'), 'leaf.png');
    assert.equal(svg.status, 415);
    assert.equal(calls, 0);
  });
});

test('field name, extra fields, and remote URL requests are rejected', async () => {
  await withServer({ geminiClient: mock() }, async base => {
    const form = new FormData();
    form.append('wrong', new Blob([await fixture()]), 'leaf.jpg');
    assert.equal((await fetch(base + '/api/analyze', { method: 'POST', body: form })).status, 422);
    const two = new FormData();
    two.append('image', new Blob([await fixture()]), 'a.jpg');
    two.append('image', new Blob([await fixture()]), 'b.jpg');
    assert.equal((await fetch(base + '/api/analyze', { method: 'POST', body: two })).status, 422);
    const json = await fetch(base + '/api/analyze', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{"url":"https://example.com/leaf.jpg"}' });
    assert.equal(json.status, 415);
  });
});

test('file limit and decoded pixel limit are enforced', async () => {
  await withServer({ env: { ...env, MAX_UPLOAD_BYTES: '1024' }, geminiClient: mock() }, async base => {
    const response = await upload(base, await fixture());
    assert.equal(response.status, 413);
    assert.equal((await response.json()).code, 'image_too_large');
  });
  await withServer({ env: { ...env, MAX_IMAGE_PIXELS: '4096' }, geminiClient: mock() }, async base => {
    const response = await upload(base, await fixture());
    assert.equal(response.status, 422);
    assert.equal((await response.json()).code, 'image_dimensions_exceeded');
  });
});

test('animated WebP is rejected', async () => {
  const pixels = Buffer.alloc(128 * 256 * 3);
  pixels.fill(220, 128 * 128 * 3);
  const webp = await sharp(pixels, { raw: { width: 128, height: 256, channels: 3, pageHeight: 128 } })
    .webp({ loop: 0, delay: [100, 100] }).toBuffer();
  assert.equal((await sharp(webp, { animated: true }).metadata()).pages, 2);
  await withServer({ geminiClient: mock() }, async base => {
    const response = await upload(base, webp, 'leaf.webp');
    assert.equal(response.status, 415);
    assert.equal((await response.json()).code, 'animated_image');
  });
});

test('per-instance request quota and explicit CORS are enforced', async () => {
  await withServer({ env: { ...env, RATE_LIMIT_PER_MINUTE: '1' }, geminiClient: mock() }, async base => {
    assert.equal((await upload(base, await fixture())).status, 200);
    const limited = await upload(base, await fixture());
    assert.equal(limited.status, 429);
    assert.ok(Number(limited.headers.get('retry-after')) > 0);
  });
  await withServer({ geminiClient: mock() }, async base => {
    const allowed = await fetch(base + '/api/health', { headers: { Origin: 'http://localhost:5173' } });
    assert.equal(allowed.headers.get('access-control-allow-origin'), 'http://localhost:5173');
    const denied = await fetch(base + '/api/health', { headers: { Origin: 'https://untrusted.example' } });
    assert.equal(denied.status, 403);
  });
});

test('provider failure is a safe non-2xx error with no fallback or secrets', async () => {
  await withServer({ geminiClient: { assess: async () => { throw new ApiError(429, 'gemini_rate_limited', 'Quota busy', 60); } } }, async base => {
    const response = await upload(base, await fixture());
    assert.equal(response.status, 429);
    const body = await response.json();
    assert.equal(body.code, 'gemini_rate_limited');
    assert.equal(body.confidence, undefined);
    assert.ok(!JSON.stringify(body).includes(env.GEMINI_API_KEY));
  });
});

test('deadline returns timeout and cannot release still-running work admission early', async () => {
  let release;
  let started;
  const startedPromise = new Promise(resolve => { started = resolve; });
  const pending = new Promise(resolve => { release = resolve; });
  await withServer({ env: { ...env, ANALYSIS_TIMEOUT_MS: '2000', MAX_CONCURRENT_ANALYSES: '1' },
    geminiClient: { assess: async () => { started(); await pending; return standardAssessment; } } }, async base => {
    const first = upload(base, await fixture());
    await Promise.race([startedPromise, new Promise((_, reject) => { const timer = setTimeout(() => reject(new Error('Mock provider did not start within the test deadline.')), 5000); timer.unref(); })]);
    const busy = await upload(base, await fixture());
    assert.equal(busy.status, 503);
    const timeout = await first;
    assert.equal(timeout.status, 504);
    assert.equal((await timeout.json()).code, 'analysis_timeout');
    const stillBusy = await upload(base, await fixture());
    assert.equal(stillBusy.status, 503);
    release();
  });
});

test('catalog marks static PlantVillage mapping as educational, including unmapped grape mildew', async () => {
  await withServer({ env: {} }, async base => {
    const entries = await (await fetch(base + '/api/plants')).json();
    assert.ok(entries.items.length >= 10);
    const grape = await (await fetch(base + '/api/plants/grape-powdery-mildew')).json();
    assert.equal(grape.plant_village_class, null);
    assert.equal(grape.model_supported, false);
    assert.equal(grape.mapping_type, 'educational_catalog_only');
    assert.equal((await fetch(base + '/api/plants/missing')).status, 404);
  });
});

test('daily paid-call cap counts actual analyses and fails closed within the instance', async () => {
  let calls = 0;
  await withServer({ env: { ...env, GEMINI_DAILY_REQUEST_LIMIT: '1' },
    geminiClient: { assess: async () => { calls++; return standardAssessment; } } }, async base => {
    assert.equal((await upload(base, await fixture())).status, 200);
    const limited = await upload(base, await fixture());
    assert.equal(limited.status, 429);
    assert.equal(calls, 1);
  });
});

test('declared oversized multipart body is rejected before the body is read', async () => {
  await withServer({ geminiClient: mock() }, async base => {
    const result = await new Promise((resolve, reject) => {
      const request = http.request(base + '/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'multipart/form-data; boundary=bounded', 'Content-Length': 9_000_000 },
      }, response => {
        const chunks = [];
        response.on('data', chunk => chunks.push(chunk));
        response.on('end', () => resolve({ status: response.statusCode, body: JSON.parse(Buffer.concat(chunks)) }));
      });
      request.on('error', reject);
      request.end();
    });
    assert.equal(result.status, 413);
    assert.equal(result.body.code, 'image_too_large');
  });
});

test('closing the client connection aborts the pending provider request', async () => {
  let started;
  let cancelled;
  const startedPromise = new Promise(resolve => { started = resolve; });
  const cancelledPromise = new Promise(resolve => { cancelled = resolve; });
  const client = { assess: async (_, { signal }) => new Promise((resolve, reject) => {
    started();
    signal.addEventListener('abort', () => {
      cancelled();
      reject(signal.reason);
    }, { once: true });
  }) };
  await withServer({ geminiClient: client }, async base => {
    const controller = new AbortController();
    const response = upload(base, await fixture(), 'leaf.jpg', { signal: controller.signal });
    await Promise.race([startedPromise, new Promise((_, reject) => { const timer = setTimeout(() => reject(new Error('Mock provider did not start within the test deadline.')), 5000); timer.unref(); })]);
    controller.abort();
    await assert.rejects(response, error => error.name === 'AbortError');
    await Promise.race([
      cancelledPromise,
      new Promise((_, reject) => { const timer = setTimeout(() => reject(new Error('Provider cancellation did not propagate.')), 1000); timer.unref(); }),
    ]);
  });
});
