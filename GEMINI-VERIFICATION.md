# Gemini-only verification - 2026-10-23

Active runtime: React/Vite + Node/Vercel API + Gemini + sourced information catalog.
No TensorFlow, model training, Python server, or GPU is used by this runtime.

- Google key authentication: accepted. Credential stored only in ignored .env.local.
- Callable model selected after latency checks: gemini-3.1-flash-lite.
- Actual leaf upload: HTTP 200; 8207 ms end-to-end.
- Actual response: possible plant Tomato; possible condition Early blight.
- Exact catalog match: tomato-early-blight; sourced care and prevention returned.
- Actual non-leaf image: HTTP 200 with unsupported_image, null plant/condition, no catalog care.
- Actual production-browser workflow: decode/compress -> upload -> scanning -> real Gemini response -> rendered result; zero page errors.
- Automated regression suite: 44 passed, 0 failed.
- Production build: passed, 36 botanical assets verified.
- Secret scan: key absent from src, server source, api source, tests, and public dist assets.
- Vercel routing and environment configuration prepared. No production deployment was performed.

The test leaf is an existing generated website illustration. This verifies a real API integration, not measured botanical diagnosis accuracy. Gemini outputs remain tentative; no accuracy or confidence claim is made.

Primary evidence: qa/gemini-live-upload.json, qa/gemini-nonleaf-result.json, qa/gemini-browser-result.txt, qa/gemini-browser-scanning.png, qa/gemini-browser-result.png.

Earlier Gemini 3.8 Flash requests timed out, so the final configuration uses the measured faster model above. Unit tests use controlled provider fixtures; they are reported separately from the live image and browser checks.
