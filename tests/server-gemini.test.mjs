import test from 'node:test';
import assert from 'node:assert/strict';
import { createGeminiClient, validateAssessment } from '../server/gemini.mjs';

const assessment = {
  contains_leaf: 'yes', image_quality: 'usable', plant: null,
  possible_condition: null, visible_symptoms: [], limitations: ['Image only'],
};
const settings = { apiKey: 'TEST-NOT-A-REAL-KEY', model: 'test-gemini-model', geminiTimeoutMs: 1000 };

test('structured Gemini validation rejects omitted, extra, unsafe, or invented fields', () => {
  assert.deepEqual(validateAssessment(structuredClone(assessment)), assessment);
  for (const invalid of [
    {}, { ...assessment, confidence: 99 }, { ...assessment, contains_leaf: 'definitely' },
    { ...assessment, visible_symptoms: ['<script>'] }, { ...assessment, visible_symptoms: ['https://invented.example'] },
    { ...assessment, plant: { common_name: 'Tomato' } },
    { ...assessment, limitations: Array(7).fill('Too much') },
  ]) assert.throws(() => validateAssessment(invalid), error => error.code === 'gemini_invalid_response');
});

test('SDK receives sanitized inline bytes, schema, cancellation, and one-call safeguards', async () => {
  const calls = [];
  const sdk = { models: { generateContent: async request => {
    calls.push(request);
    return { candidates: [{ finishReason: 'STOP' }], text: JSON.stringify(assessment) };
  } } };
  const client = createGeminiClient(settings, sdk);
  const controller = new AbortController();
  assert.deepEqual(await client.assess(Buffer.from('sanitized-image'), { signal: controller.signal }), assessment);
  assert.equal(calls.length, 1);
  const request = calls[0];
  assert.equal(request.model, settings.model);
  assert.equal(request.config.responseMimeType, 'application/json');
  assert.equal(request.config.abortSignal, controller.signal);
  assert.equal(request.config.automaticContinuation, false);
  assert.equal(request.contents[0].parts[0].inlineData.mimeType, 'image/jpeg');
  assert.equal(request.config.tools, undefined);
  assert.ok(!JSON.stringify(request).includes(settings.apiKey));
});

for (const [status, code, expected] of [
  [401, 'gemini_authentication_error', 503], [403, 'gemini_authentication_error', 503],
  [429, 'gemini_rate_limited', 429], [503, 'gemini_unavailable', 503],
]) {
  test('provider ' + status + ' is isolated and not automatically retried', async () => {
    let calls = 0;
    const client = createGeminiClient(settings, { models: { generateContent: async () => {
      calls++; throw Object.assign(new Error('PRIVATE PROVIDER ERROR'), { status });
    } } });
    await assert.rejects(client.assess(Buffer.from('image')), error => error.code === code && error.status === expected && !error.message.includes('PRIVATE'));
    assert.equal(calls, 1);
  });
}

test('refusal, malformed JSON, and truncated outputs never become successful results', async () => {
  for (const response of [
    { candidates: [{ finishReason: 'SAFETY' }], text: '' },
    { candidates: [{ finishReason: 'STOP' }], text: 'not json' },
    { candidates: [{ finishReason: 'MAX_TOKENS' }], text: JSON.stringify(assessment) },
  ]) {
    const client = createGeminiClient(settings, { models: { generateContent: async () => response } });
    await assert.rejects(client.assess(Buffer.from('image')), error => ['gemini_refused', 'gemini_invalid_response'].includes(error.code));
  }
});

test('missing key/model does not create an SDK client or fake result', () => {
  assert.equal(createGeminiClient({ ...settings, apiKey: '' }), null);
  assert.equal(createGeminiClient({ ...settings, model: '' }), null);
});

test('SDK cancellation is a safe timeout rather than malformed result', async () => {
  const controller = new AbortController();
  controller.abort();
  const client = createGeminiClient(settings, { models: { generateContent: async () => {
    throw Object.assign(new Error('aborted'), { name: 'AbortError' });
  } } });
  await assert.rejects(client.assess(Buffer.from('image'), { signal: controller.signal }), error => error.status === 504);
});
