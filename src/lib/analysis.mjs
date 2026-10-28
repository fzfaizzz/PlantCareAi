export const MAX_IMAGE_BYTES = 10 * 1024 * 1024;
export const MAX_UPLOAD_IMAGE_BYTES = 1.5 * 1024 * 1024;
const IMAGE_TYPES = { 'image/jpeg': ['jpg', 'jpeg'], 'image/png': ['png'], 'image/webp': ['webp'] };
const RESULT_STATUSES = ['success', 'uncertain', 'unsupported_image'];

export class AnalysisError extends Error {
  constructor(message, code = 'analysis', options = {}) {
    super(message);
    this.name = 'AnalysisError';
    this.code = code;
    this.status = options.status;
    this.requestId = options.requestId || null;
  }
}
export function validateImageFile(file) {
  if (!file) return { ok: false, error: 'Choose a leaf image first.' };
  if (!Number.isFinite(file.size) || file.size <= 0) return { ok: false, error: 'This file is empty or unreadable. Choose another image.' };
  if (file.size > MAX_IMAGE_BYTES) return { ok: false, error: 'This image is too large. Choose a file no larger than 10 MiB.' };
  const extensions = IMAGE_TYPES[file.type?.toLowerCase()];
  const extension = String(file.name || '').split('.').pop().toLowerCase();
  if (!extensions || !extensions.includes(extension)) return { ok: false, error: 'Choose a JPG, PNG or WebP image with a matching file extension.' };
  return { ok: true, error: null };
}
export function resolveAnalysisEndpoint(value, origin = 'http://localhost') {
  const input = String(value || '/api/analyze').trim() || '/api/analyze';
  if (input.startsWith('//') || input.includes('\\')) throw new AnalysisError('The analysis endpoint must use HTTPS or a local development server.', 'configuration');
  let endpoint;
  try { endpoint = new URL(input, origin); }
  catch { throw new AnalysisError('The analysis endpoint is not a valid URL.', 'configuration'); }
  const local = ['localhost', '127.0.0.1', '[::1]'].includes(endpoint.hostname);
  if (endpoint.username || endpoint.password || endpoint.hash || (endpoint.protocol !== 'https:' && !(endpoint.protocol === 'http:' && local))) throw new AnalysisError('The analysis endpoint must use HTTPS or a local development server, without embedded credentials.', 'configuration');
  return endpoint.href;
}
function invalid(field) { throw new AnalysisError(`The analysis service returned an invalid ${field} field. Please try again.`, 'response'); }
function record(value, field) { if (!value || typeof value !== 'object' || Array.isArray(value)) invalid(field); return value; }
function text(value, field, nullable = false, limit = 4000) {
  if (nullable && (value === null || value === undefined)) return null;
  if (typeof value !== 'string' || !value.trim() || value.length > limit) invalid(field);
  return value.trim();
}
function list(value, field, limit = 30) { if (!Array.isArray(value) || value.length > limit) invalid(field); return value.map(item => text(item, field)); }
function source(value) {
  record(value, 'source');
  let url;
  try { url = new URL(value.url); } catch { invalid('source URL'); }
  if (url.protocol !== 'https:' || url.username || url.password) invalid('source URL');
  return { title: text(value.title || value.name, 'source title', false, 400), url: url.href, attribution: text(value.attribution || value.publisher, 'source attribution', true, 600) };
}
/** Gemini assessment has no fabricated numeric confidence or trained-classifier scores. */
export function validateAnalysisResponse(payload) {
  record(payload, 'result');
  if (payload.schema_version !== '2.0') invalid('schema version');
  if (!RESULT_STATUSES.includes(payload.status)) invalid('result status');
  if (payload.confidence !== null) invalid('confidence; no numeric confidence is supplied by this assessment');
  const provider = record(payload.provider, 'provider');
  if (provider.name !== 'gemini') invalid('provider name');
  const catalog = record(payload.catalog, 'catalog');
  if (typeof catalog.matched !== 'boolean') invalid('catalog match');
  const care = list(payload.care || [], 'care'), prevention = list(payload.prevention || [], 'prevention');
  const generalGuidance = list(payload.general_guidance || [], 'general guidance');
  const generalGuidanceSource = payload.general_guidance_source ? source(payload.general_guidance_source) : null;
  if (generalGuidance.length && !generalGuidanceSource) invalid('general guidance source');
  if (!catalog.matched && (care.length || prevention.length)) invalid('unattributed care');
  if (payload.status === 'success' && !payload.plant) invalid('plant hypothesis');
  const timings = {};
  for (const [key, value] of Object.entries(record(payload.timings_ms || {}, 'timings'))) {
    if (!/^[a-z][a-z0-9_]{0,39}$/i.test(key) || typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > 3_600_000) invalid('processing timings');
    timings[key] = value;
  }
  return {
    schema_version: '2.0', request_id: text(payload.request_id, 'request identifier', false, 128), status: payload.status,
    plant: text(payload.plant, 'plant hypothesis', true, 200), condition: text(payload.condition, 'condition hypothesis', true, 300), confidence: null,
    provider: { name: 'gemini', model: text(provider.model, 'Gemini model', false, 200) },
    observations: list(payload.observations || [], 'image observations'), care, prevention, general_guidance: generalGuidance, general_guidance_source: generalGuidanceSource,
    uncertainty: text(payload.uncertainty, 'uncertainty', true), explanation: text(payload.explanation, 'explanation', true),
    catalog: { matched: catalog.matched, slug: text(catalog.slug, 'catalog slug', true, 200), plant_village_class: text(catalog.plant_village_class, 'PlantVillage category reference', true, 200) },
    sources: Array.isArray(payload.sources) && payload.sources.length <= 30 ? payload.sources.map(source) : invalid('sources'),
    warnings: list(payload.warnings || [], 'warnings'), timings_ms: timings,
  };
}

/** Decode uses the browser's EXIF orientation; canvas re-encoding removes metadata. */
export async function compressDecodedImage(image, { signal, canvasFactory = () => document.createElement('canvas') } = {}) {
  const width = image.naturalWidth || image.width, height = image.naturalHeight || image.height;
  if (!Number.isInteger(width) || !Number.isInteger(height) || width <= 0 || height <= 0 || width * height > 20_000_000 || Math.max(width, height) > 20_000) throw new AnalysisError('Resize this photo to 20 megapixels or fewer and try again.', 'file');
  if (signal?.aborted) throw new DOMException('Image preparation cancelled.', 'AbortError');
  const canvas = canvasFactory();
  const scale = Math.min(1, 1600 / Math.max(width, height));
  let targetWidth = Math.max(1, Math.round(width * scale)), targetHeight = Math.max(1, Math.round(height * scale));
  const encode = quality => new Promise((resolve, reject) => {
    let finished = false;
    const finish = (error, blob) => { if (finished) return; finished = true; signal?.removeEventListener('abort', abort); error ? reject(error) : resolve(blob); };
    const abort = () => finish(new DOMException('Image preparation cancelled.', 'AbortError'));
    signal?.addEventListener('abort', abort, { once: true });
    if (signal?.aborted) { abort(); return; }
    try { canvas.toBlob(blob => { if (!blob || !blob.size) finish(new AnalysisError('This image could not be prepared. Try another photo.', 'file')); else finish(null, blob); }, 'image/jpeg', quality); }
    catch { finish(new AnalysisError('This image could not be prepared. Try another photo.', 'file')); }
  });
  try {
    for (let attempt = 0; attempt < 5; attempt += 1) {
      if (signal?.aborted) throw new DOMException('Image preparation cancelled.', 'AbortError');
      canvas.width = targetWidth; canvas.height = targetHeight;
      const context = canvas.getContext('2d', { alpha: false });
      if (!context) throw new AnalysisError('Your browser cannot prepare this photo. Try a different browser.', 'file');
      context.fillStyle = '#ffffff'; context.fillRect(0, 0, canvas.width, canvas.height);
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      const blob = await encode(attempt === 0 ? 0.86 : 0.72);
      if (signal?.aborted) throw new DOMException('Image preparation cancelled.', 'AbortError');
      if (blob.size <= MAX_UPLOAD_IMAGE_BYTES) return new File([blob], 'leaf-analysis.jpg', { type: 'image/jpeg' });
      targetWidth = Math.max(1, Math.round(targetWidth * 0.75)); targetHeight = Math.max(1, Math.round(targetHeight * 0.75));
    }
    throw new AnalysisError('This photo could not be reduced enough for upload. Resize it and try again.', 'file');
  } finally { canvas.width = 0; canvas.height = 0; }
}

export function validatePlantGuide(payload, slug) {
  record(payload, 'plant guide');
  if (payload.slug !== slug) invalid('plant guide slug');
  return { slug, plant: text(payload.plant, 'guide plant', false, 200), condition: text(payload.condition, 'guide condition', false, 300), symptoms: list(payload.symptoms || [], 'guide symptoms'), care: list(payload.care || [], 'guide care'), prevention: list(payload.prevention || [], 'guide prevention'), sources: Array.isArray(payload.sources) && payload.sources.length <= 20 ? payload.sources.map(source) : invalid('guide sources'), attribution: text(payload.attribution, 'guide attribution', true, 600) };
}
export async function requestPlantGuide({ slug, endpoint, origin, signal, fetchImpl = globalThis.fetch }) {
  if (!/^[a-z0-9-]{1,100}$/.test(slug)) throw new AnalysisError('This plant guide is unavailable.', 'catalog');
  const url = new URL(`./plants/${slug}`, resolveAnalysisEndpoint(endpoint, origin));
  const response = await fetchImpl(url.href, { headers: { Accept: 'application/json' }, signal });
  if (!response.ok) throw new AnalysisError('The online guide is unavailable. The saved educational guide is shown.', 'catalog');
  const raw = await response.text();
  if (raw.length > 100_000) invalid('plant guide');
  return validatePlantGuide(JSON.parse(raw), slug);
}

const PUBLIC_ERRORS = {
  analysis_unavailable: 'Image analysis is not configured. The project owner needs to configure GEMINI_API_KEY and GEMINI_MODEL on the server.',
  gemini_authentication_error: 'The Google Gemini credentials need attention. Please contact the project owner.',
  gemini_rate_limited: 'The Gemini quota is currently reached. Please wait before trying again.',
  gemini_invalid_response: 'The AI assessment was incomplete. Try another clear leaf image.',
  gemini_refused: 'This image could not be assessed. Try a clear photo of a leaf.',
  analysis_timeout: 'Image analysis took too long. Please try again.',
  service_busy: 'Another image is being processed. Please try again shortly.',
  unsupported_image_format: 'Choose a still JPG, PNG or WebP leaf photo.',
  poor_quality_image: 'This photo has too little visible detail. Choose a clearer, well-lit leaf photo.',
  image_dimensions_exceeded: 'Resize this photo to 20 megapixels or fewer and try again.',
  animated_image: 'Choose a still image. Animated photos are not supported.',
  service_unavailable: 'The image analysis service is temporarily unavailable. Please try again shortly.',
  gemini_unavailable: 'Google Gemini is temporarily unavailable. Please try again shortly.',
  gemini_not_configured: 'Image analysis is not configured. The project owner needs to configure the server-side Gemini key.',
  configuration_error: 'Image analysis is not configured. The project owner needs to check the server settings.',
  rate_limited: 'The request limit has been reached. Please wait before trying again.',
  quota_exceeded: 'The Gemini request limit has been reached. Please wait before trying again.',
  authentication_error: 'The analysis service credentials need attention. Please contact the project owner.',
  invalid_image: 'This image could not be decoded safely. Choose a clear JPG, PNG or WebP photo.',
  image_too_large: 'This image could not be reduced enough for upload. Choose a smaller photo.',
  unsupported_image: 'This image cannot be analyzed. Please choose a clear, still photo of a leaf.',
  analysis_failed: 'The service could not assess this photo. Try another clear leaf image.',
  invalid_response: 'The AI assessment was incomplete. Try another clear leaf image.',
  refused: 'This image could not be assessed. Try a clear photo of a leaf.',
};
function httpError(xhr) {
  let payload;
  try { payload = JSON.parse(xhr.responseText); } catch { /* Gateways can return non-JSON errors. */ }
  const error = payload?.error || payload;
  const candidateCode = error?.code;
  const code = typeof candidateCode === 'string' && /^[a-z_]{1,60}$/.test(candidateCode) ? candidateCode : 'http';
  const requestId = typeof (error?.request_id || payload?.request_id) === 'string' ? (error.request_id || payload.request_id).slice(0, 128) : null;
  const fallback = xhr.status === 413 ? PUBLIC_ERRORS.image_too_large : xhr.status === 415 ? PUBLIC_ERRORS.unsupported_image : xhr.status === 429 ? PUBLIC_ERRORS.rate_limited : xhr.status === 503 ? PUBLIC_ERRORS.service_unavailable : `The analysis service returned an error (${xhr.status}). Please try again.`;
  return new AnalysisError(PUBLIC_ERRORS[code] || fallback, code, { status: xhr.status, requestId });
}
/** XHR exposes genuine upload events. The pending scan is indeterminate, never a guessed server percentage. */
export function requestAnalysis({ file, endpoint, signal, xhrFactory = () => new XMLHttpRequest(), onPhase = () => {}, onUploadProgress = () => {}, timeoutMs = 60_000, origin }) {
  return new Promise((resolve, reject) => {
    const check = validateImageFile(file);
    if (!check.ok) { reject(new AnalysisError(check.error, 'file')); return; }
    let url;
    try { url = resolveAnalysisEndpoint(endpoint, origin); } catch (error) { reject(error); return; }
    if (!url) { reject(new AnalysisError('Analysis is not configured. Set VITE_ANALYSIS_ENDPOINT to the running backend and restart the frontend.', 'configuration')); return; }
    if (signal?.aborted) { reject(new DOMException('Analysis cancelled.', 'AbortError')); return; }
    let xhr;
    let settled = false;
    let analyzing = false;
    const finish = (error, result) => {
      if (settled) return;
      settled = true;
      signal?.removeEventListener('abort', abort);
      if (xhr) {
        xhr.onload = xhr.onerror = xhr.ontimeout = xhr.onabort = xhr.onreadystatechange = null;
        xhr.upload.onprogress = xhr.upload.onload = null;
      }
      if (error) { onPhase(error.name === 'AbortError' ? 'cancelled' : 'error'); reject(error); }
      else { onPhase('success'); resolve(result); }
    };
    const beginAnalyzing = () => {
      if (!settled && !analyzing && !signal?.aborted) { analyzing = true; onPhase('analyzing'); }
    };
    const abort = () => { xhr?.abort(); finish(new DOMException('Analysis cancelled.', 'AbortError')); };
    try {
      xhr = xhrFactory();
      xhr.open('POST', url, true);
      xhr.setRequestHeader('Accept', 'application/json');
      xhr.timeout = timeoutMs;
      xhr.withCredentials = false;
      xhr.upload.onprogress = event => {
        if (settled || signal?.aborted || analyzing) return;
        onUploadProgress(event.lengthComputable && event.total > 0 ? Math.max(0, Math.min(100, Math.round(event.loaded / event.total * 100))) : null);
      };
      xhr.upload.onload = beginAnalyzing;
      xhr.onreadystatechange = () => { if (xhr.readyState >= 2) beginAnalyzing(); };
      xhr.onload = () => {
        if (signal?.aborted) { finish(new DOMException('Analysis cancelled.', 'AbortError')); return; }
        if (xhr.status < 200 || xhr.status >= 300) { finish(httpError(xhr)); return; }
        if (!xhr.responseText || xhr.responseText.length > 1_000_000) { finish(new AnalysisError('The analysis service returned unreadable data. Please try again.', 'response')); return; }
        try { finish(null, validateAnalysisResponse(JSON.parse(xhr.responseText))); }
        catch (error) { finish(error instanceof AnalysisError ? error : new AnalysisError('The analysis service returned unreadable data. Please try again.', 'response')); }
      };
      xhr.onerror = () => finish(new AnalysisError('Unable to reach the analysis service. Check that the backend is running and its allowed origins include this site.', 'network'));
      xhr.ontimeout = () => finish(new AnalysisError('Analysis took too long. Please try again.', 'timeout'));
      xhr.onabort = () => finish(new DOMException('Analysis cancelled.', 'AbortError'));
      signal?.addEventListener('abort', abort, { once: true });
      if (signal?.aborted) { abort(); return; }
      const body = new FormData();
      body.append('image', file, file.name);
      onUploadProgress(null);
      onPhase('uploading');
      xhr.send(body);
    } catch (error) {
      finish(error instanceof AnalysisError ? error : new AnalysisError('Unable to start the analysis request. Please try again.', 'network'));
    }
  });
}




