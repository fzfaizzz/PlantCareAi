import { createHash, randomUUID } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { ApiError } from './errors.mjs';
import { readMultipartImage, normalizeImage } from './image.mjs';
import { createGeminiClient, validateAssessment } from './gemini.mjs';
import { assembleResult, listPlants, findPlant } from './catalog.mjs';

function boundedNumber(value, fallback, min, max) {
  const n = Number(value);
  return Number.isFinite(n) && n >= min && n <= max ? n : fallback;
}

export function readSettings(env = process.env) {
  return {
    apiKey: String(env.GEMINI_API_KEY || '').trim(),
    model: String(env.GEMINI_MODEL || '').trim(),
    maxFileBytes: boundedNumber(env.MAX_UPLOAD_BYTES, 4 * 1024 * 1024, 1024, 4 * 1024 * 1024),
    maxRequestBytes: Math.floor(4.3 * 1024 * 1024),
    maxImagePixels: boundedNumber(env.MAX_IMAGE_PIXELS, 20_000_000, 4096, 20_000_000),
    uploadTimeoutMs: boundedNumber(env.UPLOAD_TIMEOUT_MS, 20_000, 100, 30_000),
    geminiTimeoutMs: boundedNumber(env.GEMINI_TIMEOUT_MS, 40_000, 100, 45_000),
    analysisTimeoutMs: boundedNumber(env.ANALYSIS_TIMEOUT_MS, 50_000, 100, 55_000),
    maxConcurrent: boundedNumber(env.MAX_CONCURRENT_ANALYSES, 2, 1, 4),
    requestsPerMinute: boundedNumber(env.RATE_LIMIT_PER_MINUTE, 12, 1, 120),
    dailyCallsPerInstance: boundedNumber(env.GEMINI_DAILY_REQUEST_LIMIT, 100, 1, 10000),
    trustProxyHeaders: env.TRUST_PROXY_HEADERS === 'true' || env.VERCEL === '1',
    origins: String(env.FRONTEND_ORIGINS || 'http://127.0.0.1:5173,http://localhost:5173')
      .split(',').map(value => value.trim().replace(/\/$/, '')).filter(value => value && value !== '*'),
  };
}

function json(res, status, body, requestId, extra = {}) {
  if (res.destroyed || res.writableEnded) return;
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
    'X-Request-ID': requestId,
    ...extra,
  });
  res.end(JSON.stringify(body));
}

class LocalQuota {
  constructor() { this.buckets = new Map(); }
  take(key, maximum, seconds) {
    const now = Date.now();
    if (this.buckets.size > 2000) {
      for (const [bucket, value] of this.buckets) if (value.expires <= now) this.buckets.delete(bucket);
      if (this.buckets.size > 2000 && !this.buckets.has(key)) {
        throw new ApiError(429, 'rate_limited', 'The image service is busy. Please try again.', 60);
      }
    }
    const current = this.buckets.get(key);
    const value = current && current.expires > now ? current : { count: 0, expires: now + seconds * 1000 };
    value.count += 1;
    this.buckets.set(key, value);
    if (value.count > maximum) throw new ApiError(429, 'rate_limited', 'Too many image requests. Please try later.', Math.max(1, Math.ceil((value.expires - now) / 1000)));
  }
}

function allowedOrigin(req, settings) {
  const origin = req.headers.origin;
  if (!origin) return null;
  try {
    if (new URL(origin).host === req.headers.host || settings.origins.includes(origin)) return origin;
  } catch { /* Malformed origins do not receive CORS authorization. */ }
  throw new ApiError(403, 'origin_not_allowed', 'This origin is not allowed to use the image service.');
}

export function createApiHandler({ env = process.env, geminiClient, logger = console } = {}) {
  const settings = readSettings(env);
  const gemini = geminiClient || createGeminiClient(settings);
  const quota = new LocalQuota();
  let active = 0;
  return async function apiHandler(req, res, next) {
    const path = new URL(req.url || '/', 'http://localhost').pathname.replace(/\/$/, '');
    if (!path.startsWith('/api/')) {
      if (next) return next();
      return json(res, 404, { code: 'not_found', message: 'API endpoint not found.' }, randomUUID());
    }
    const requestId = randomUUID();
    const started = performance.now();
    let responseStatus = 500;
    const controller = new AbortController();
    let deadline;
    const abort = () => controller.abort(new ApiError(499, 'cancelled', 'The image request was cancelled.'));
    const close = () => { if (!res.writableFinished) abort(); };
    req.once('aborted', abort);
    res.once('close', close);
    try {
      const origin = allowedOrigin(req, settings);
      if (origin) {
        res.setHeader('Access-Control-Allow-Origin', origin);
        res.setHeader('Vary', 'Origin');
        res.setHeader('Access-Control-Expose-Headers', 'X-Request-ID, Retry-After');
      }
      if (req.method === 'OPTIONS') {
        res.writeHead(204, { 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type', 'Access-Control-Max-Age': '600' });
        res.end();
        responseStatus = 204;
        return;
      }
      if (req.method === 'GET') {
        let body;
        if (path === '/api/health') {
          body = {
            schema_version: '2.0', status: 'ok',
            provider: { name: 'gemini', model: settings.model || null,
              configured: Boolean(settings.apiKey && settings.model), live_verified: false },
            limits: { max_upload_bytes: settings.maxFileBytes, max_image_pixels: settings.maxImagePixels,
              max_concurrent_analyses: settings.maxConcurrent, quota_scope: 'per_instance',
              requests_per_minute: settings.requestsPerMinute, daily_calls_per_instance: settings.dailyCallsPerInstance },
            privacy: { image_retention: 'No image storage or training collection.',
              sends_image_to_google: true, google_terms_url: 'https://ai.google.dev/gemini-api/terms' },
          };
        } else if (path === '/api/model-info') {
          body = {
            schema_version: '2.0', provider: { name: 'gemini', model: settings.model || null },
            inference_type: 'gemini_image_interpretation', tensorflow_enabled: false,
            trained_classifier: false, numeric_confidence: false,
            plant_village_usage: 'Educational class-name mapping only; no dataset, training, or TensorFlow runtime.',
            catalog_entries: listPlants().length,
            limitations: ['Plant and condition identities are tentative image hypotheses.',
              'No exhaustive tree coverage or measured disease-classification accuracy is claimed.'],
          };
        } else if (path === '/api/plants') {
          body = { schema_version: '2.0', items: listPlants() };
        } else if (path.startsWith('/api/plants/')) {
          body = findPlant(decodeURIComponent(path.slice('/api/plants/'.length)));
          if (!body) throw new ApiError(404, 'plant_not_found', 'The requested educational condition entry was not found.');
        } else throw new ApiError(404, 'not_found', 'API endpoint not found.');
        responseStatus = 200;
        json(res, 200, body, requestId);
        return;
      }
      if (path !== '/api/analyze') throw new ApiError(404, 'not_found', 'API endpoint not found.');
      if (req.method !== 'POST') throw new ApiError(405, 'method_not_allowed', 'Use POST to analyze an image.');
      const address = settings.trustProxyHeaders ? String(req.headers['x-forwarded-for'] || req.socket?.remoteAddress || '').split(',')[0].trim() : req.socket?.remoteAddress || '';
      quota.take('ip:' + createHash('sha256').update(address).digest('hex'), settings.requestsPerMinute, 60);
      if (active >= settings.maxConcurrent) throw new ApiError(503, 'service_busy', 'Another image is being processed. Try again shortly.', 2);
      active += 1;
      deadline = setTimeout(() => controller.abort(new ApiError(504, 'analysis_timeout', 'Image analysis timed out. Please try again.')), settings.analysisTimeoutMs);
      deadline.unref?.();
      const work = (async () => {
        const uploadStarted = performance.now();
        const raw = await readMultipartImage(req, settings, controller.signal);
        const uploadMs = performance.now() - uploadStarted;
        const decodeStarted = performance.now();
        const image = await normalizeImage(raw, settings);
        if (controller.signal.aborted) throw controller.signal.reason;
        if (!gemini) throw new ApiError(503, 'analysis_unavailable', 'Configure GEMINI_API_KEY and GEMINI_MODEL on the server to enable real image analysis.');
        quota.take('gemini:daily', settings.dailyCallsPerInstance, 86400);
        const providerStarted = performance.now();
        const assessment = validateAssessment(await gemini.assess(image.jpeg, { signal: controller.signal }));
        if (controller.signal.aborted) throw controller.signal.reason;
        return assembleResult(assessment, image, {
          requestId, model: settings.model,
          timings: { upload: Math.round(uploadMs), decode: Math.round(providerStarted - decodeStarted),
            provider: Math.round(performance.now() - providerStarted), total: Math.round(performance.now() - started) },
        });
      })().finally(() => { active -= 1; });
      // If a decoder/SDK ignores cancellation, its admission slot stays occupied until it settles.
      const aborted = new Promise((_, reject) => controller.signal.addEventListener('abort', () => reject(controller.signal.reason), { once: true }));
      const result = await Promise.race([work, aborted]);
      responseStatus = 200;
      json(res, 200, result, requestId);
    } catch (error) {
      const safe = error instanceof ApiError ? error : new ApiError(500, 'internal_error', 'The image service could not process this request.');
      responseStatus = safe.status;
      req.resume();
      json(res, safe.status, { code: safe.code, message: safe.message, request_id: requestId }, requestId,
        safe.retryAfter ? { 'Retry-After': String(safe.retryAfter) } : {});
    } finally {
      clearTimeout(deadline);
      req.off('aborted', abort);
      res.off('close', close);
      // No image, filename, key, IP address, or provider error payload enters logs.
      logger.info?.(JSON.stringify({ event: 'api_request', request_id: requestId,
        method: req.method, path, status: responseStatus, duration_ms: Math.round(performance.now() - started) }));
    }
  };
}

export function createVercelHandler(options = {}) { return createApiHandler(options); }
