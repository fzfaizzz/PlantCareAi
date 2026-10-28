# PlantCare AI - Streamlit

The active Python interface is `streamlit_app.py`. Home, Plant Library, About, profile controls, image upload and results are implemented in Streamlit, using the existing local botanical artwork and green/cream design. It runs without React, Node, Vite, or a separate API server. The previous React source is preserved for recovery; see [README-REACT.md](README-REACT.md) for that older version.

## Run the converted application

This checkout already has the required packages in `backend/.venv`:

```powershell
cd C:\Users\akhta\Downloads\PlantCareAi
.\backend\.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Open http://127.0.0.1:8501. The Python server must remain running. The old React preview at port 5173 is a separate application and will not show these changes.

For a fresh, independent installation, use Python 3.13 (tested with 3.13.5):

```powershell
cd C:\Users\akhta\Downloads\PlantCareAi
py -3.13 -m venv .venv-streamlit
.\.venv-streamlit\Scripts\python.exe -m pip install -r requirements-streamlit.txt
.\.venv-streamlit\Scripts\python.exe -m streamlit run streamlit_app.py
```

`./scripts/start-streamlit.ps1` also launches the application with the available project environment. A GPU and TensorFlow are not needed for this Gemini-based version.

## Private configuration

The existing ignored root `.env.local` file is reused by the Python application:

```dotenv
GEMINI_API_KEY=your_private_server_key
GEMINI_MODEL=gemini-3.1-flash-lite
GEMINI_TIMEOUT_SECONDS=40
PLANTCARE_ANALYSIS_ENGINE=auto
```

Actual environment variables override the local file. The model must be available to the configured account and accept images and structured output. No key is included in browser source, response data, screenshots, or logs. Never put it in a `VITE_` setting. Keep `.env.local` and `.streamlit/secrets.toml` out of Git.

## What is converted

- One shared rounded navbar with native Streamlit Home, Plant Library and About navigation, and a green About button.
- Botanical Home hero, an animated/draggable image strip, hand-drawn notes and a Detect a Leaf anchor that scrolls to the native detection section. Direct detection view: `?page=Detect`.
- Native file uploader, Pillow image checks and metadata removal, illustrative sample selection, actual Gemini pending animation, sourced results and a temporary text history (up to 20 results per session).
- Native library search, one plant filter, responsive guide cards and sourced care dialogs. About describes the actual Python/Streamlit/Pillow/Gemini stack.
- Local fonts, illustrations, sample hover effects, entrance/preloader styling and reduced-motion support.

Streamlit renders its own widgets, so this is a native port with the approved visual language, rather than an embedded React website. Browser-specific column wrapping and widget appearance can differ from React. Streamlit supports smooth anchor navigation; the former Lenis library is not required.

## Real image flow

1. Choose a JPEG, PNG or WebP image (10 MiB maximum; still images only).
2. Python/Pillow checks decoded content, dimensions (20 MP maximum), image mode and EXIF orientation. A fresh RGB JPEG up to 1600 pixels removes original metadata.
3. Select **Detect Disease**. This explicit action sends the sanitized photo to Google Gemini; ordinary Streamlit reruns and filter changes never make paid analysis calls.
4. Gemini produces validated tentative plant/condition names, visible symptoms and limitations. Application code matches those names to the local sourced care catalog.
5. The interface shows the actual response, uncertainty and references. Unmatched conditions get clearly labelled general checks rather than invented treatment. Non-leaf and uncertain images have distinct outcomes. Errors never produce demo diagnoses or confidence numbers.

The scan is indeterminate and lasts only while the real provider request is pending. No percentage, fake upload stage or timed diagnosis is shown. The synchronous native request has a bounded provider timeout; navigating away does not guarantee cancellation of an already running provider request. Do not assume the React abort behavior applies to this native application.

Photos travel to the Python server and, after Detect Disease, to Google Gemini when cloud assessment is configured. Selected image bytes remain in the current Streamlit session until removed; they are not written to disk. Text history lasts only for that session. There is no server authentication or persistent user database.

Library and sample photos are generated illustrations, not evidence of classification accuracy. Care content comes from the references stored in `plantcare_streamlit/data/catalog.json`; Gemini does not supply source URLs.

## Tests

```powershell
.\backend\.venv\Scripts\python.exe -m pytest tests_streamlit -q
```

Tests cover corrupt/disguised/oversized/animated images, orientation and metadata removal, provider errors and malformed responses, tentative/catalog policies, native navigation, library search/filtering, profile controls, sample selection and removal. Mock provider tests do not prove diagnostic accuracy. The dedicated live check report in `qa/streamlit-verification.json`, when present, documents the actual image request performed separately.

## Hosting

The converted app needs a persistent Python Streamlit host, such as Streamlit Community Cloud or a container/VM with WebSocket support. Vercel's static React build does not host this Python interface. Keep the old Vercel configuration only if retaining the previous React app separately.

Use `streamlit_app.py` as the application entry point, install root `requirements.txt`, and set `GEMINI_API_KEY` and `GEMINI_MODEL` privately in the host's environment/secret settings. For Community Cloud, top-level secret keys can be supplied via its secrets panel. No production deployment has been performed in this conversion.

## Analysis mode and result boundaries

`PLANTCARE_ANALYSIS_ENGINE=auto` prefers the configured Gemini image assessment. `gemini` requires that provider and returns a safe error if unavailable. `local` keeps photos on the Python server. In auto mode, provider failure can use the local comparison, with the failure disclosed in assessment notes; it cannot become a confirmed disease result.

A saved MobileNetV2 bundle exists in `models/` with 8 labels across Apple, Corn, Potato and Tomato. This task did not train or evaluate that bundle. No calibration, held-out evaluation or unknown-plant rejection evidence accompanies it. Its preprocessing includes an embedded 1/255 rescaling; inference passes RGB values in 0–255 without applying normalization again.

Every output from this unvalidated local bundle is **inconclusive**. Its nearest labels and actual scores are available only in assessment notes, clearly marked as dataset comparisons. A score such as 40.4/100 is not a 40.4% probability of disease, and a higher score alone cannot establish an unfamiliar species. Old local results already in a browser session use the same policy on rerender and download.

Gemini provides tentative plant/condition hypotheses and observations from the image; code matches names to the sourced information catalog. Catalog symptoms are never presented as observations of the uploaded leaf. Uncertain or unmatched assessments receive general next steps rather than disease-specific treatment. Healthy-looking foliage does not rule out hidden problems. No numeric Gemini confidence is invented, and no model accuracy is claimed.

The library contains 10 educational guides for five plants; these are not identical to the local classifier labels. Its reference pictures are generated illustrations. No training, measured diagnostic accuracy or production deployment was completed in this change.
