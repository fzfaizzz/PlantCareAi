import test from 'node:test';
import assert from 'node:assert/strict';
import { MAX_IMAGE_BYTES, MAX_UPLOAD_IMAGE_BYTES, compressDecodedImage, requestAnalysis, requestPlantGuide, resolveAnalysisEndpoint, validateAnalysisResponse, validateImageFile, validatePlantGuide } from '../src/lib/analysis.mjs';

const leaf = () => new File(['test transport bytes, not a model/photo accuracy sample'], 'leaf.webp', { type: 'image/webp' });
const successfulResult = () => ({
 schema_version: '2.0', request_id: 'fixture-request-123', status: 'uncertain', plant: 'Tomato', condition: 'Possible leaf spots', confidence: null,
 general_guidance: [], general_guidance_source: null, provider: { name: 'gemini', model: 'test-fixture-only' }, observations: ['Pale areas visible'], care: ['Avoid wetting foliage'], prevention: [], uncertainty: 'A photo cannot establish the cause.', explanation: 'Mocked transport fixture, not a live AI assessment.',
 catalog: { matched: true, slug: 'tomato-early-blight', plant_village_class: 'Tomato___Early_blight' },
 sources: [{ title: 'Extension source fixture', url: 'https://extension.example/plant-care', attribution: null }], warnings: ['This fixture does not establish diagnostic accuracy.'], timings_ms: { total: 20 },
});
class FixtureXHR {
 constructor(send) { this.upload = {}; this.sendFixture = send; this.status = 200; this.responseText = ''; this.readyState = 0; this.headers = {}; this.aborted = false; }
 open(method, url, async) { Object.assign(this, { method, url, async }); }
 setRequestHeader(key, value) { this.headers[key] = value; }
 send(body) { this.body = body; this.sendFixture?.(this); }
 abort() { this.aborted = true; this.onabort?.(); }
 respond(payload = successfulResult(), status = 200) { this.status = status; this.responseText = typeof payload === 'string' ? payload : JSON.stringify(payload); this.readyState = 4; this.onreadystatechange?.(); this.onload?.(); }
}
const request = (options = {}) => requestAnalysis({ file: leaf(), endpoint: 'https://analysis.example/api/analyze', ...options });

test('upload validation accepts supported originals up to 10 MiB and rejects empty, disguised and oversized files', () => {
 assert.equal(validateImageFile(leaf()).ok, true);
 assert.equal(validateImageFile({ name: 'photo.JPEG', type: 'image/jpeg', size: MAX_IMAGE_BYTES }).ok, true);
 for (const invalid of [null, { name: 'empty.png', type: 'image/png', size: 0 }, { name: 'oversize.png', type: 'image/png', size: MAX_IMAGE_BYTES + 1 }, { name: 'script.svg', type: 'image/svg+xml', size: 20 }, { name: 'mislabelled.jpg', type: 'image/png', size: 20 }, { name: 'leaf.png', type: '', size: 20 }, { name: 'leaf.png', type: 'image/png', size: Infinity }]) assert.equal(validateImageFile(invalid).ok, false);
});
test('same-origin endpoint is the default; credentials, unsafe schemes and external HTTP are rejected', () => {
 assert.equal(resolveAnalysisEndpoint(undefined, 'https://plants.example'), 'https://plants.example/api/analyze');
 assert.equal(resolveAnalysisEndpoint('', 'https://plants.example'), 'https://plants.example/api/analyze');
 assert.equal(resolveAnalysisEndpoint('http://127.0.0.1:8000/api/analyze'), 'http://127.0.0.1:8000/api/analyze');
 for (const endpoint of ['http://plants.example/analyze', 'javascript:alert(1)', 'file:///tmp/upload', 'https://user:secret@plants.example/api', '//third-party.example/api', 'https://plants.example/api#secret', 'https:\\plants.example']) assert.throws(() => resolveAnalysisEndpoint(endpoint), { code: 'configuration' });
});
test('v2 retains tentative Gemini observations, references and matched care without inventing confidence', () => {
 const payload = successfulResult();
 assert.deepEqual(validateAnalysisResponse({ ...payload, unexpected: '<script>ignored</script>' }), payload);
 const result = validateAnalysisResponse({ ...payload, sources: [{ title: 'Source', url: 'https://extension.example/', publisher: 'Extension publisher' }] });
 assert.equal(result.confidence, null);
 assert.equal(result.sources[0].attribution, 'Extension publisher');
 assert.equal('top_predictions' in result, false);
 assert.equal('model' in result, false);
});
test('unsupported outcomes contain no invented diagnosis and unmatched care is forbidden', () => {
 const payload = { ...successfulResult(), status: 'unsupported_image', plant: null, condition: null, care: [], catalog: { matched: false, slug: null, plant_village_class: null } };
 assert.equal(validateAnalysisResponse(payload).condition, null);
 assert.throws(() => validateAnalysisResponse({ ...payload, care: ['Invented cure'] }), { code: 'response' });
});
test('old classifier/demo results, numeric AI confidence, malformed contracts and unsafe sources are rejected', () => {
 for (const payload of [null, [], {}, { plant: 'Tomato' }, { ...successfulResult(), schema_version: '1.0' }, { ...successfulResult(), status: 'healthy' }, { ...successfulResult(), confidence: 98 }, { ...successfulResult(), care: 'Care' }, { ...successfulResult(), care: [null] }, { ...successfulResult(), provider: { name: 'unknown', model: 'unknown' } }, { ...successfulResult(), provider: null }, { ...successfulResult(), catalog: { matched: 'yes' } }, { ...successfulResult(), sources: [{ title: 'Unsafe', url: 'javascript:alert(1)' }] }, { ...successfulResult(), status: 'success', plant: null }]) assert.throws(() => validateAnalysisResponse(payload), { code: 'response' });
});
test('XHR multipart reports only genuine upload percentage; pending AI scan has no simulated percentage', async () => {
 const phases = [], percentages = [];
 let received;
 const result = await request({ onPhase: phase => phases.push(phase), onUploadProgress: percent => percentages.push(percent), xhrFactory: () => new FixtureXHR(xhr => {
  received = xhr;
  assert.deepEqual(phases, ['uploading']);
  xhr.upload.onprogress({ lengthComputable: false, loaded: 1, total: 0 });
  xhr.upload.onprogress({ lengthComputable: true, loaded: 128, total: 256 });
  xhr.upload.onprogress({ lengthComputable: true, loaded: 256, total: 256 });
  xhr.upload.onload();
  xhr.upload.onprogress({ lengthComputable: true, loaded: 1, total: 2 });
  xhr.respond();
 }) });
 assert.equal(received.body.get('image').name, 'leaf.webp');
 assert.equal(received.headers['Content-Type'], undefined);
 assert.equal(received.withCredentials, false);
 assert.deepEqual(percentages, [null, null, 50, 100]);
 assert.deepEqual(phases, ['uploading', 'analyzing', 'success']);
 assert.deepEqual(result, successfulResult());
});
test('response headers start pending scan even when upload completion events are missing', async () => {
 const phases = [];
 await request({ onPhase: phase => phases.push(phase), xhrFactory: () => new FixtureXHR(xhr => xhr.respond()) });
 assert.deepEqual(phases, ['uploading', 'analyzing', 'success']);
});
test('invalid file and invalid endpoint never create a network request', async () => {
 let calls = 0; const xhrFactory = () => { calls += 1; };
 await assert.rejects(request({ endpoint: 'javascript:alert(1)', xhrFactory }), { code: 'configuration' });
 await assert.rejects(request({ file: null, xhrFactory }), { code: 'file' });
 assert.equal(calls, 0);
});
test('Gemini configuration failure shows safe actionable error and request id, never server secrets', async () => {
 await assert.rejects(request({ xhrFactory: () => new FixtureXHR(xhr => xhr.respond({ error: { code: 'analysis_unavailable', message: 'secret key/path', request_id: 'backend-reference-1' } }, 503)) }), error => {
  assert.equal(error.code, 'analysis_unavailable'); assert.equal(error.requestId, 'backend-reference-1'); assert.match(error.message, /GEMINI_API_KEY/); assert.doesNotMatch(error.message, /secret|path/); return true;
 });
});
test('413, 415, quota, gateway, malformed JSON and network errors cannot become successful assessments', async () => {
 for (const [action, code] of [[xhr => xhr.respond({}, 413), 'http'], [xhr => xhr.respond({}, 415), 'http'], [xhr => xhr.respond({ code: 'gemini_rate_limited', request_id: 'quota-id' }, 429), 'gemini_rate_limited'], [xhr => xhr.respond('<html>gateway secret</html>', 502), 'http'], [xhr => xhr.respond('bad json'), 'response'], [xhr => xhr.onerror(), 'network']]) {
  const phases = [];
  await assert.rejects(request({ onPhase: phase => phases.push(phase), xhrFactory: () => new FixtureXHR(action) }), { code });
  assert.equal(phases.at(-1), 'error'); assert.equal(phases.includes('success'), false);
 }
});
test('cancellation aborts upload and suppresses late responses', async () => {
 const controller = new AbortController(), phases = []; let xhr;
 const operation = request({ signal: controller.signal, onPhase: phase => phases.push(phase), xhrFactory: () => (xhr = new FixtureXHR()) });
 const lateResponse = xhr.onload; controller.abort(); await assert.rejects(operation, { name: 'AbortError' });
 assert.equal(xhr.aborted, true); assert.equal(xhr.onload, null); xhr.responseText = JSON.stringify(successfulResult()); lateResponse();
 assert.deepEqual(phases, ['uploading', 'cancelled']);
});
test('timeout and pre-cancelled operations cannot publish a result', async () => {
 await assert.rejects(request({ timeoutMs: 17, xhrFactory: () => new FixtureXHR(xhr => { assert.equal(xhr.timeout, 17); xhr.ontimeout(); }) }), { code: 'timeout' });
 const controller = new AbortController(); controller.abort(); let calls = 0;
 await assert.rejects(request({ signal: controller.signal, xhrFactory: () => { calls += 1; } }), { name: 'AbortError' }); assert.equal(calls, 0);
});

function fixtureCanvas(sizes, callback) {
 const draws = [], encodes = [];
 const canvas = { width: 0, height: 0, getContext: () => ({ fillRect: () => {}, drawImage: (...args) => draws.push(args), set fillStyle(_value) {} }), toBlob: (done, type, quality) => { encodes.push({ width: canvas.width, height: canvas.height, type, quality }); if (callback) callback(done); else done(new Blob([new Uint8Array(sizes.shift() || 20)], { type })); } };
 return { canvas, draws, encodes };
}
test('browser preparation fits within 1600px without upscaling and always re-encodes metadata-free JPEG', async () => {
 for (const [width, height, expected] of [[4000, 3000, [1600, 1200]], [300, 600, [300, 600]]]) {
  const { canvas, encodes } = fixtureCanvas([200]);
  const file = await compressDecodedImage({ naturalWidth: width, naturalHeight: height }, { canvasFactory: () => canvas });
  assert.equal(file.name, 'leaf-analysis.jpg'); assert.equal(file.type, 'image/jpeg'); assert.ok(file.size <= MAX_UPLOAD_IMAGE_BYTES);
  assert.deepEqual([encodes[0].width, encodes[0].height], expected); assert.equal(encodes[0].type, 'image/jpeg'); assert.equal(canvas.width, 0); assert.equal(canvas.height, 0);
 }
});
test('preparation reduces oversized output, bounds attempts, and rejects excessive pixel counts', async () => {
 const { canvas, encodes } = fixtureCanvas([MAX_UPLOAD_IMAGE_BYTES + 1, 500]);
 assert.equal((await compressDecodedImage({ width: 1600, height: 1200 }, { canvasFactory: () => canvas })).size, 500);
 assert.equal(encodes.length, 2); assert.equal(encodes[1].width, 1200);
 await assert.rejects(compressDecodedImage({ width: 6000, height: 6000 }), { code: 'file' });
});
test('cancelling preparation rejects immediately and ignores the late encoder callback', async () => {
 const controller = new AbortController(); let encodeDone;
 const { canvas } = fixtureCanvas([], done => { encodeDone = done; });
 const operation = compressDecodedImage({ width: 1600, height: 1200 }, { signal: controller.signal, canvasFactory: () => canvas });
 controller.abort(); await assert.rejects(operation, { name: 'AbortError' });
 encodeDone(new Blob(['late bytes'], { type: 'image/jpeg' })); assert.equal(canvas.width, 0);
});
test('failed encoder produces an actionable error and releases the canvas', async () => {
 const { canvas } = fixtureCanvas([], done => done(null));
 await assert.rejects(compressDecodedImage({ width: 100, height: 100 }, { canvasFactory: () => canvas }), { code: 'file' }); assert.equal(canvas.width, 0);
});

const guide = () => ({ slug: 'tomato-healthy', plant: 'Tomato', condition: 'Healthy', symptoms: ['Even leaves'], care: ['Monitor changes'], prevention: [], sources: [{ title: 'Guide', url: 'https://extension.example/tomato', attribution: null }], attribution: 'Curated care reference, not photo observations.' });
test('catalog lookup uses endpoint API base and retains sourced guide fields', async () => {
 let url;
 const result = await requestPlantGuide({ slug: 'tomato-healthy', endpoint: 'https://plants.example/api/analyze', fetchImpl: async value => { url = value; return { ok: true, text: async () => JSON.stringify(guide()) }; } });
 assert.equal(url, 'https://plants.example/api/plants/tomato-healthy'); assert.deepEqual(result, guide());
});
test('catalog offline, stale slug and unsafe sources cause saved educational fallback rather than bad data', async () => {
 await assert.rejects(requestPlantGuide({ slug: 'tomato-healthy', fetchImpl: async () => ({ ok: false }) }), { code: 'catalog' });
 assert.throws(() => validatePlantGuide(guide(), 'apple-scab'), { code: 'response' });
 assert.throws(() => validatePlantGuide({ ...guide(), sources: [{ title: 'Bad', url: 'javascript:bad()' }] }, 'tomato-healthy'), { code: 'response' });
 let calls = 0; await assert.rejects(requestPlantGuide({ slug: '../secrets', fetchImpl: async () => { calls += 1; } }), { code: 'catalog' }); assert.equal(calls, 0);
});



test('unmatched general guidance remains separate from condition care and requires a safe source', () => {
 const payload = { ...successfulResult(), care: [], prevention: [], catalog: { matched: false, slug: null, plant_village_class: null }, general_guidance: ['Inspect nearby leaves.'], general_guidance_source: { title: 'Plant assessment guide', url: 'https://apps.extension.umn.edu/garden/diagnose/plant/', publisher: 'University extension' } };
 const result = validateAnalysisResponse(payload);
 assert.equal(result.care.length, 0); assert.equal(result.catalog.matched, false); assert.equal(result.general_guidance_source.attribution, 'University extension');
 assert.throws(() => validateAnalysisResponse({ ...payload, general_guidance_source: null }), { code: 'response' });
 assert.throws(() => validateAnalysisResponse({ ...payload, general_guidance_source: { title: 'Unsafe', url: 'javascript:bad()' } }), { code: 'response' });
});

test('actual server v2 producer satisfies the frontend boundary for matched, unmatched, uncertain and non-leaf assessments', async () => {
 const { assembleResult } = await import('../server/catalog.mjs');
 for (const [plant, condition, containsLeaf, quality] of [['Tomato', 'Healthy', 'yes', 'usable'], ['Mango', 'Leaf discoloration', 'yes', 'usable'], [null, null, 'uncertain', 'poor'], [null, null, 'no', 'usable']]) {
  const payload = assembleResult({ plant: plant ? { common_name: plant, scientific_name: null } : null, possible_condition: condition, contains_leaf: containsLeaf, image_quality: quality, visible_symptoms: [], limitations: [] }, { qualityWarnings: [] }, { requestId: 'contract-test-only', model: 'fixture-only', timings: { total: 3 } });
  const result = validateAnalysisResponse(payload);
  assert.equal(result.confidence, null);
  if (!result.catalog.matched) assert.equal(result.care.length, 0);
  if (containsLeaf === 'no') assert.equal(result.status, 'unsupported_image');
 }
});
