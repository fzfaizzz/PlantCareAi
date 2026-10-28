# PlantCare AI

PlantCare AI uses the Google Gemini API to assess leaf photos, then matches the possible plant and condition against a sourced educational catalog. No model training, TensorFlow runtime, GPU, or separate Python service is required.

## Run locally

Use Node.js 22 and npm. From PowerShell:

```powershell
cd C:\Users\akhta\Downloads\PlantCareAi
npm.cmd install
npm.cmd run dev
```

Open http://127.0.0.1:5173. The same Vite process serves the website and local `/api` endpoints.

Create an ignored `.env.local` file if one does not exist:

```dotenv
VITE_ANALYSIS_ENDPOINT=/api/analyze
GEMINI_API_KEY=your_private_key
GEMINI_MODEL=gemini-3.1-flash-lite
```

The configured model must be available to the supplied API key and support image input plus structured JSON. Listing a model does not necessarily mean a new account may invoke it; verify an actual image request. Restart Vite after changing environment settings.

Never prefix the key with `VITE_`, put it into frontend source, or commit it. Browser requests go to the app's own API, which calls Google with a private server-side key.

## How it works

1. Select or drop a JPEG, PNG, or WebP leaf image, up to 10 MiB.
2. The browser checks the decoded image and compresses it into a JPEG up to 1600 pixels / 1.5 MiB, stripping metadata.
3. The Node API validates the real image content, limits decoded pixels and request size, and sanitizes it again.
4. Gemini returns possible plant/condition names, visible observations, image-quality information, and limitations as validated structured JSON.
5. Code matches the names to the local catalog. Condition-specific care is shown only for a matching catalog entry. General guidance, where available, is labelled separately.
6. The frontend displays the real response. Upload progress is measured; scanning is indeterminate while the actual request is pending. Cancel/replace/remove abort the request and ignore stale answers.

Possible identifications are AI interpretations, not confirmed diagnoses. No numeric confidence or measured classification accuracy is invented. Unsupported/non-leaf images and uncertain photos have distinct outcomes. API failures never produce sample diagnoses.

PlantVillage is used only for educational category-name mapping. It is not a live lookup API, is not queried on each request, and does not provide the care catalog. There is no dataset download or training step in this application.

## API

- `GET /api/health`: configuration and safe public limits; no key exposure.
- `GET /api/model-info`: Gemini capabilities and honest limitations.
- `GET /api/plants`: sourced educational entries.
- `GET /api/plants/:slug`: a single educational entry.
- `POST /api/analyze`: multipart field `image`; versioned `2.0` result.

The health endpoint's `configured` flag means the key/model are present; it is not a live credentials or quota check. The live image test report, when present in `qa/`, records the actual verification performed during setup.

The API accepts at most 4 MiB per sanitized file and bounds the multipart body below Vercel's 4.5 MB function payload limit. Browser compression keeps normal uploads well below this limit. Originals above 20 million decoded pixels are rejected with a clear size message.

## Build and test

```powershell
npm.cmd test
npm.cmd run build
npm.cmd run preview
```

Unit tests inject provider responses to check parsing, errors, and application behavior without spending API quota. They are not evidence of disease accuracy. Live checks use the actual Google service and consume its quota.

## Deploy on Vercel

1. Import this project as Vite, with Node.js 22, build `npm run build`, and output `dist`.
2. Set private environment variables `GEMINI_API_KEY` and `GEMINI_MODEL` in the Vercel project.
3. Set `VITE_ANALYSIS_ENDPOINT=/api/analyze` or keep the frontend's same-origin default.
4. Deploy and test `/api/health`, an actual image upload, `/library`, and `/about` page refreshes.

The `api/[...path].mjs` Node function reuses `server/`. SPA rewrites exclude API routes. Do not deploy the earlier Python experimental backend; `.vercelignore` excludes it.

Local `.env.local` values are deliberately not uploaded to Vercel. Configure the production secrets in Vercel and redeploy after changes. No production deployment is claimed by the local setup.

## Operational notes

- Gemini calls are bounded by request deadlines, image/output limits, and a small local concurrency gate.
- Request quotas are **per running instance**, not a guaranteed account-wide spending limit on an autoscaling host. Configure project/API quotas and Vercel firewall/rate controls before public exposure. A future shared limiter is needed for a strict global request budget.
- Optional settings include `GEMINI_TIMEOUT_MS`, `ANALYSIS_TIMEOUT_MS`, `RATE_LIMIT_PER_MINUTE`, `GEMINI_DAILY_REQUEST_LIMIT`, and `FRONTEND_ORIGINS`. Inspect `server/index.mjs` for bounds/defaults.
- Images are processed in memory and sent inline to Google. This app does not save them or add them to a training dataset. Google's handling follows the applicable account/service terms: https://ai.google.dev/gemini-api/terms
- Login/signup currently create only a browser-local profile; they are not server accounts.
- Botanical website assets are AI-generated illustrations, not evidence of model accuracy.
- Existing `backend/` files belong to the discontinued TensorFlow implementation attempt. They are unused by the npm/Vercel runtime and can be retained solely for recovery. No Python package installation or backend startup is required.

## Troubleshooting

- Missing configuration: set the two server-only Gemini variables and restart/redeploy.
- Authentication failure: verify the key's Gemini API permissions; never send the key in a support screenshot.
- Quota/rate error: check the Google project's applicable quota/billing, then retry later.
- Model unavailable: select a currently callable image/JSON-capable Gemini model for that key.
- Timeout: try a clear single-leaf photo; check the configured provider deadline.
- Unknown condition: a catalog miss is not proof of plant health. The app preserves Gemini observations and reports the limitation.
