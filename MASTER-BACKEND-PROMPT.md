> SUPERSEDED: The user chose Gemini API + catalog only. Do not execute the TensorFlow/training instructions below. See README.md for the active architecture.

# PLANTCARE AI - REAL BACKEND, TENSORFLOW AND GEMINI MASTER PROMPT

## Objective and working boundaries

Transform the EXISTING PlantCare AI application into a working, deployable plant-health application with a real backend and real model inference. Implement the work in phases, rather than replying with a plan only.

The project currently lives at:
C:\Users\akhta\Downloads\PlantCareAi

Inspect the actual checkout before changing anything. Preserve the approved frontend. Do not replace it with a template or introduce unnecessary libraries. The attached older full-stack prompt is background; this document and the user's latest approved UI take precedence.

A working demo UI, an executable training script, and a trained/evaluated classifier are three different deliverables. Report each truthfully. Do not mark the entire project complete while training, credentials, actual API integration, or deployment verification is still outstanding.

## 1. Existing implementation to preserve and intedgrate

The frontend uses React, Vite, React Router, plain CSS, Lenis, lucide-react, and locally hosted fonts. Inspect package.json for exact installed versions. Keep these choices; do not add Tailwind, Framer Motion, Next.js, or another scrolling library simply because an older prompt mentioned them.

Approved behavior:
- One shared rounded navbar: Home, Plant Library, About, plus account controls.
- The Home hero fills the screen without side gutters, and its curved carousel supports dragging.
- Detect a Leaf scrolls to the full-screen detection section below Home. Direct /detect also works.
- Plant Library, About, the branded 3D-style preloader, existing images, reduced-motion support, and responsive layouts remain intact.
- Removed page badges must remain removed.
- Existing profile controls currently store a LOCAL browser profile. Do not represent them as real server authentication or build an unrelated auth system.

Inspect and reuse these integration points:
- src/components/ImageUploader.jsx
- src/lib/analysis.mjs
- src/pages/DetectPage.jsx and src/pages/HomePage.jsx
- src/pages/LibraryPage.jsx and src/data/plants.js or the actual catalog file
- src/pages/AboutPage.jsx
- src/components/SmoothScrolling.jsx
- src/components/Preloader.jsx and preloader.css
- src/reference.css and src/navbar.css
- .env.example and vercel.json

The existing frontend variable is VITE_ANALYSIS_ENDPOINT. Reuse it unless a documented migration is necessary. It currently posts FormData with the field name image. The current response validator only retains limited fields; extend it explicitly when adding statuses, sources, top alternatives, and model metadata.

ImageUploader currently contains timed preview-only scanning and a demo result. Inspect the actual code. These simulations MUST NOT remain in the production inference path. Preserve the polished visuals, replacing the timers with actual file-reading, upload, request, and result events. The site preloader has a separate asset-loading lifecycle and should remain separate from analysis.

## 2. Correct architecture

Use:
1. Existing React/Vite frontend on Vercel.
2. Python FastAPI backend packaged as a Linux Docker container; prepare Google Cloud Run deployment as the reference deployment.
3. TensorFlow/Keras trained classifier for supported plant-condition classes.
4. An explicit curated condition-information catalog for symptoms, general care, prevention, and references.
5. Optional server-side Gemini image interpretation and explanation using the official google-genai SDK.

Processing:
Browser image -> backend validation -> normalized image -> trained classifier + optional Gemini assessment -> uncertainty/conflict policy -> curated information -> validated JSON -> existing results interface.

PlantVillage is a training dataset, NOT a live diagnostic API. TensorFlow runs a trained model; it does not fetch a disease answer from PlantVillage on every request. Gemini does not turn PlantVillage into an all-tree identification database.

Run the classifier across its actual trained classes. Do not require Gemini to guess a plant first and then force the classifier into that plant's classes. An incorrect Gemini guess must not determine the TensorFlow answer.

Gemini may provide a tentative plant/crop identity, visible observations, and image limitations. Its image assessment should be made independently of the classifier scores if it will be used for disagreement checking. Use at most one image-assessment call per analysis by default. The backend can assemble explanations from its structured assessment and curated catalog without another mandatory LLM call.

Gemini is optional enrichment, not a required dependency for the trained classifier. If it is disabled, unavailable, or rate-limited, valid TensorFlow classification and curated care still work. If the trained model is missing, return model_unavailable; do not silently substitute Gemini or demo predictions.

## 3. Honest support boundaries and result policy

A closed-set crop classifier cannot establish the identity or health of every tree. The application must distinguish:
- Supported, sufficiently reliable classifier prediction.
- Uncertain or conflicting interpretation.
- Unsupported input or unsupported plant hypothesis.
- Invalid/poor-quality image.
- Unavailable model/service.

Rules:
- A healthy class means the image resembles that dataset class; it does not rule out every disease, pest, nutrient issue, or other problem.
- Low uncertainty is not established merely because softmax has a high score.
- Do not use a single confidence threshold as proof of reliable unknown-species rejection.
- If Gemini suggests a plant outside the trained scope, preserve it as an unverified hypothesis and flag a potential scope mismatch. Do not state that the species was conclusively identified.
- Do not automatically relabel an unsupported tree as the closest supported crop.
- Keep TensorFlow top classes and Gemini hypotheses separate. Never average their scores or force agreement.
- Significant plant/condition conflict should downgrade the overall interpretation to uncertain.
- Missing or incomplete Gemini output is unavailable/unknown, not a successful confirmation.
- No fake confidence numbers, invented metrics, fabricated model weights, or hardcoded disease diagnoses.

## 4. PlantVillage preparation

Starting source:
https://www.tensorflow.org/datasets/catalog/plant_village

The catalog currently documents 54,303 images, 38 combined plant/condition categories, and one train split. These are NOT 38 diseases and NOT coverage of every plant. The downloaded builder metadata and ordered labels are authoritative.

Build executable preparation, training, and evaluation commands. Preparation must:
- Inspect TFDS version, builder version, labels, filenames, counts, and class imbalance.
- Record the download source, dataset provenance, licensing/usage terms, and checksums where available. Do not confuse the documentation website's license with the dataset license.
- Check for invalid images and exact duplicates; group near duplicates or related source images where practical.
- Produce deterministic, class-stratified train/validation/test manifests. Keep duplicate groups in one split. Use an explicit seed and document any classes too small for a requested split.
- Split BEFORE augmentation. Never distribute augmented copies of the same image across splits.
- Preserve the label-index ordering used to train the classifier.
- Cache downloads and save reproducible metadata/manifests; do not commit the dataset to Git.

Do not treat TFDS train as a pre-existing clean train/validation/test benchmark. If source grouping information is unavailable, document the remaining leakage risk rather than claiming it has been eliminated.

## 5. Model training and artifact integrity

Start with MobileNetV2 transfer learning at 224 x 224 RGB unless repository evidence supports a better lightweight alternative. Do not start with a very large model.

Use a compatible TensorFlow/Keras/Python combination verified against current official documentation. Pin the working dependency set after a clean installation check. For Windows, support CPU inference locally and supply a compatible Linux/Colab GPU training workflow. Do not promise current TensorFlow GPU support on native Windows without checking compatibility.

Training:
- Seed randomness where practical; record environment and reproducibility limitations.
- Frozen pretrained backbone plus a classification head matching the actual ordered classes.
- Training-only augmentation and appropriate class weighting if useful.
- Early stopping and best-validation checkpoints.
- Optional controlled fine-tuning after the initial head is trained.
- One consistent preprocessing implementation shared by training and inference. Apply the backbone normalization exactly once. Record RGB conversion, resize/crop policy, range, input size, and output semantics.
- Do not apply softmax twice or independently sort classes during inference.

Save a versioned artifact bundle:
- plant_disease_model.keras
- class_labels.json
- model_metadata.json
- validation-derived decision policy/calibration parameters, when available
- artifact checksums
- training history, per-class evaluation, confusion matrix, and test report

Validate input/output shapes and ordered label count when loading the artifact. Load trusted model artifacts only, once per backend process at startup. Reject mismatched or corrupt bundles.

Evaluate held-out accuracy, macro F1, per-class precision/recall, confusion, and score reliability. Select uncertainty thresholds with validation data, not the test set. Report dataset test results separately from field-photo validation. Include a separate, permitted set of actual phone/field photos and non-leaf/out-of-scope images where available. Never use generated website illustrations as proof of real-world model accuracy.

If training cannot run here, finish the executable pipeline, provide a runnable notebook and artifact-import instructions, and clearly mark model training/inference acceptance as blocked. Do not fabricate a checkpoint to make tests pass.

## 6. Gemini integration

Official sources:
https://ai.google.dev/gemini-api/docs/image-understanding
https://ai.google.dev/gemini-api/docs/structured-output

Keep GEMINI_API_KEY exclusively on the backend. Select an available image-capable model using GEMINI_MODEL; verify current model and structured-output support rather than hardcoding a model copied from an old tutorial.

Send only a safely decoded, resized image with metadata removed. Prefer inline image data for the initial implementation; do not create persistent external file uploads unnecessarily. Clearly disclose when the user's image is sent to Google, and document the selected service's applicable data-use policy. Never claim that an image stays in the browser when real analysis is enabled.

Use a small Pydantic-validated structured response with nullable/unknown values, such as:
- contains_leaf: yes / no / uncertain
- plant_hypothesis: common_name and optional scientific_name, or null
- image_quality: usable / poor / uncertain
- visible_symptoms: string array
- condition_hypothesis: string or null
- limitations: string array

Do not request an invented numeric confidence from Gemini. Structured JSON validates shape, not factual correctness; validate semantics too.

Treat uploaded image text and any embedded instructions as untrusted content. Do not give the Gemini assessment tools, browsing, arbitrary URL fetching, or authority to override backend policies. No model-generated executable HTML.

Bound input size, output tokens, timeout, concurrency, and retries. Handle refusals, malformed/empty output, 401/403, 429, timeouts, and 5xx responses. Retry only suitable transient failures with a small bounded backoff and Retry-After support where available. A permanent authentication failure should not be retried repeatedly.

Keep observations, curated care, and AI explanation separately attributed in the API response. Gemini must not invent source URLs or supply unsupported pesticide dosage instructions.

## 7. Backend APIs and response contract

Suggested layout; adapt to the real repo:
backend/
  app/main.py
  app/core/config.py
  app/api/health.py
  app/api/analysis.py
  app/api/plants.py
  app/schemas/analysis.py
  app/services/image_service.py
  app/services/model_service.py
  app/services/gemini_service.py
  app/services/analysis_service.py
  app/services/plant_info_service.py
  app/data/plant_diseases.json
  ml/prepare_dataset.py
  ml/train_model.py
  ml/evaluate_model.py
  models/.gitkeep
  reports/.gitkeep
  tests/
  Dockerfile
  .env.example
  requirements.txt
  requirements-training.txt
  README.md

Separate serving dependencies from training dependencies where useful. Do not install TFDS and training tooling into a production image unless needed at runtime.

Required endpoints:
- GET /api/health: API liveness and honest model/Gemini state; no secrets.
- GET /api/ready: 200 only when required model initialization succeeds, otherwise 503.
- GET /api/model-info: safe model version, ordered supported labels, preprocessing summary, genuine evaluation metadata, limitations.
- GET /api/plants and GET /api/plants/{slug}: sourced information catalog.
- POST /api/analyze: multipart field image, one image per request.

Use a versioned Pydantic response contract and a matching frontend validator. Retain compatible top-level plant, condition, symptoms, care, prevention, uncertainty fields where useful. Explicitly add:
- schema_version, request_id
- status: success / uncertain / unsupported_image
- model: version, predicted_class, score_type, calibration status
- confidence: 0-100 classifier score, nullable; never present it as guaranteed disease probability
- top_predictions with actual class scores
- Gemini enrichment status, separate plant/condition hypotheses and visible observations
- explanation, warnings, source references, and processing timings

Missing model/service failures should use an appropriate non-2xx status and a safe error body: code, message, request_id. Do not return success with a fake result. Invalid upload, too-large file, rate limit, unavailable service, and inference failure must have distinct handling. Inconclusive analysis is a valid explicit outcome, not an exception disguised as a healthy result.

Catalog entries must map to exact trained class IDs. Current decorative library entries may not match PlantVillage classes; derive model_supported from the actual mapping. Keep unrelated entries educational. Reuse existing university-extension references where appropriate and verify new sources before adding them.

## 8. Upload safety, resource limits, and runtime reliability

- Accept JPEG, PNG, and WebP after inspecting decoded content, not just the filename.
- Enforce the 10 MiB file limit and a bounded total multipart request size while streaming/reading. Do not buffer an unbounded request before checking size.
- Bound decoded pixels, dimensions, and supported image modes; handle EXIF orientation and decompression-bomb errors.
- Normalize to RGB and strip metadata before inference or sending to Gemini.
- Define a clear policy for animated/multi-frame images; reject unsupported cases.
- Do not accept arbitrary remote image URLs or untrusted model uploads.
- Close temporary/spooled files and release image buffers on success, errors, and cancellations.
- Process in memory or bounded temporary storage; do not retain images or add them to training without an explicit feature and consent.
- Run CPU inference away from FastAPI's event loop with bounded concurrency. Start with one worker and a measured memory budget so multiple workers do not duplicate model RAM unexpectedly.
- Use structured logs, request IDs, timings, and safe public errors; never log keys or image contents.
- Restrict CORS to configured origins. CORS is not authentication or abuse prevention.
- Add enforceable request/cost/concurrency limits. For multiple instances, do not present a per-process limiter as a global quota; use a shared or platform-backed limiter and document it.
- Keep Gemini enrichment disabled until its server key and model are deliberately configured. Add an operational switch to disable it without losing core classification.

## 9. Real frontend request lifecycle

Preserve the current upload UI, scanning beam, result transitions, sample-card interactions, and approved geometry.

Connect:
idle -> validating/reading -> uploading/request pending -> analyzing/request pending -> success / uncertain / unsupported / error / cancelled.

- Start real analysis after selection as the existing flow does, unless an explicit user control is required by the implementation.
- Remove the fixed preparation/scan delays and preview-result branch from the production path.
- Show file-read/decode activity only while it is occurring.
- If real upload percentage is required, use a transport supporting upload progress, such as XMLHttpRequest. Fetch alone does not provide normal browser upload progress events.
- With a single request and no server progress channel, use an indeterminate pending scan. Do not pretend to know the backend's exact percentage or internal stage.
- Keep the beam running while the real request is pending; stop immediately when the response arrives, errors, or is cancelled. Do not delay a completed answer just to finish a decorative timer.
- Replacing/removing an image or leaving the page must cancel the request and ignore late/stale results. Explain that browser cancellation does not always stop an inference already executing on the server; server timeouts/concurrency limits still apply.
- A newer selected image must never display the older image's result.
- Render actual status, source attribution, top classes, and uncertainty. Do not show a green confirmed-disease card for uncertain results.
- When a model is missing, show an actionable unavailable state, not the old animated demo result.
- If preserving a demo mode for developer previews, it must be explicitly configured and visibly labelled, with production default off.
- Update privacy text and About claims to match the enabled backend.

## 10. Configuration and deployment

Frontend .env.example:
VITE_ANALYSIS_ENDPOINT=http://127.0.0.1:8000/api/analyze

Backend .env.example (adapt implementation names):
APP_ENV=development
API_HOST=127.0.0.1
API_PORT=8000
FRONTEND_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
MODEL_PATH=models/plant_disease_model.keras
MODEL_METADATA_PATH=models/model_metadata.json
CLASS_LABELS_PATH=models/class_labels.json
MAX_UPLOAD_MB=10
MAX_IMAGE_PIXELS=20000000
GEMINI_ENABLED=false
GEMINI_API_KEY=
GEMINI_MODEL=
ANALYSIS_TIMEOUT_SECONDS=45

Use an additional configuration artifact for thresholds selected by validation; do not pretend arbitrary example thresholds are scientifically established.

Do not put the Gemini key into any VITE_ variable, frontend bundle, public health response, or repository. Use ignored local environment files and the deployment platform's secret facility.

Deployment design:
- Vercel builds and serves the existing static frontend.
- Cloud Run serves the FastAPI/TensorFlow container with the actual model bundle.
- Configure VITE_ANALYSIS_ENDPOINT to the public HTTPS backend endpoint at frontend build time.
- Browser image requests go directly to that backend. Do not unnecessarily route 10 MiB image bodies through a Vercel Function; verify current platform request limits before choosing any proxy.
- Preserve Vercel SPA rewrites for page refreshes; do not let them rewrite genuine API requests into index.html.
- Load model artifacts at startup from a versioned trusted bundle or a verified artifact source. Do not train or download PlantVillage during an API request or every cold start.
- Provide readiness/startup probes, an appropriate port binding, memory/concurrency measurements, and cold-start documentation.
- Keep training outside the serving container. Use compatible Linux/Colab training if local Windows resources are unsuitable, then import and verify the trained artifact.
- Measure memory and latency before claiming a hosting tier is sufficient. Do not promise free or unlimited deployment.
- Preserve the existing site while preparing backend deployment. Do not claim it has been deployed without testing the actual production URLs.

## 11. Implementation sequence and verification

1. Inspect repo and describe current frontend/backend/model state. Make a targeted version-control snapshot before major changes if Git is available.
2. Add backend config, schemas, validation, catalog, liveness/readiness, and meaningful tests.
3. Build and run dataset preparation; inspect metadata and split manifests.
4. Train and evaluate the actual model, or deliver the executable training notebook and report the exact external blocker.
5. Load and verify the real artifact; implement inference and the uncertainty policy.
6. Add optional Gemini integration with structured validation and failure isolation.
7. Replace the frontend demo path with the real endpoint and real lifecycle.
8. Verify upload, cancellation, image replacement, supported/uncertain/out-of-scope cases, and responsive results.
9. Prepare Docker/Cloud Run deployment, Vercel frontend configuration, and end-to-end documentation.

Tests must cover real failure modes rather than mirror implementation details:
- Empty, corrupt, disguised, oversized, decompression-heavy, and unsupported images.
- Missing/corrupt model and inconsistent label/preprocessing metadata.
- Valid inference response with real artifacts when available; mark artifact-dependent tests separately if absent.
- Unknown input, low-quality photo, uncertain score policy, and TF/Gemini conflict.
- Gemini disabled, quota failure, refusal, malformed JSON, timeout, authentication error, and network failure.
- Frontend stale response protection, cancel/remove/replace, and backend error rendering.
- Actual upload to the running backend and a production frontend build.

Mocked Gemini tests and a synthetic classifier fixture may validate plumbing, but must never be presented as proof that the production model was trained or that disease classification works. Keep paid API tests optional and clearly labelled. Document any actual live Gemini check separately.

Supply exact Windows PowerShell setup/run instructions, Linux/Docker instructions, model-training and artifact-import commands, environment configuration, and troubleshooting. Use the actual resulting module paths, not hypothetical commands.

## 12. Definition of done and final report

Distinguish implemented code, local tests, trained model, validated accuracy, configured Gemini, and production deployment.

Acceptance requires:
- Approved UI and shared navbar remain intact.
- Dataset preparation is reproducible and its class scope is documented.
- The serving process loads a genuine trained model with matching metadata.
- Supported predictions and uncertainty behavior are verified with real requests.
- Gemini enrichment is optional, secure, and cannot silently override classifier results.
- Disease care is sourced and clearly attributed.
- Upload/scanning states follow actual work, with working cancellation and no invented progress.
- No credentials are exposed, and error/resource limits work.
- Frontend build, relevant backend tests, and upload integration checks pass.
- The deployment guide reflects the selected hosts and actual model requirements.

Final report: changed files, installed versions, working endpoints, dataset version, training actually completed or not, genuine evaluation results, live Gemini test status, tests run, launch commands, deployment status, and remaining external dependencies.

Do not stop at scaffolding if real work can continue. Do not invent results if external credentials, model training, or compute are unavailable. Finish unaffected work and give precise next steps for the remaining dependency.

## Official reference starting points

Verify current documentation at implementation time:
- PlantVillage: https://www.tensorflow.org/datasets/catalog/plant_village
- Dataset archive: https://data.mendeley.com/datasets/tywbtsjrjv/1
- Gemini images: https://ai.google.dev/gemini-api/docs/image-understanding
- Gemini structured outputs: https://ai.google.dev/gemini-api/docs/structured-output
- TensorFlow installation: https://www.tensorflow.org/install/pip
- Keras MobileNet: https://keras.io/api/applications/mobilenet/
- Vercel function limits: https://vercel.com/docs/functions/limitations
- Cloud Run memory: https://docs.cloud.google.com/run/docs/configuring/services/memory-limits
