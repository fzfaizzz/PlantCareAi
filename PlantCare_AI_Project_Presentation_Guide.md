# PlantCare AI — Comprehensive Project Presentation & Viva Defense Handbook

**Autonomous Plant Pathology Detection & Organic Agricultural Advisory System Using Deep Learning**  
*Academic Year: 2025 – 2026 | Department of Information Technology*  
*Document Version: 3.0 (Master Edition for Examination Defense)*

---

## 📋 Executive Overview & Quick Pitch
- **What is PlantCare AI?**  
  An accessible, edge-compatible deep learning web application that accurately diagnoses crop diseases directly from leaf photographs and provides organic remedies and cultural prevention steps without requiring cloud GPUs or laboratory equipment.
- **Key Performance Metrics:**
  - **Neural Architecture:** MobileNetV2 (Depthwise Separable Convolutions + Inverted Residuals)
  - **Empirical Test Accuracy:** **81.25%** on authentic PlantVillage benchmark field photos
  - **Inference Latency:** &lt; 50ms on standard student laptop CPUs
  - **Model File Size:** Only **20.35 MB** (3.4 Million parameters vs 25M in ResNet-50)
  - **Supported Botanical Scope:** 8 core agricultural classes (Apple, Corn, Potato, Tomato)
  - **Execution Mode:** 100% Offline Local Engine (Zero cloud API dependency)

---

## 🏛️ 1. College Synopsis Modules Compliance Matrix

Every module specified in the college synopsis has an exact implementation in the codebase:

| Synopsis Module | Academic Requirement | Implementation File & Function | Technical Rationale |
| :--- | :--- | :--- | :--- |
| **Module 1: User Interface** | Image upload, camera input, and result display | `plantcare_streamlit/detect.py`<br>`plantcare_streamlit/services.py` | Drag-and-drop dropzone and camera capture with zero learning curve for farmers. |
| **Module 2: Preprocessing** | Resize to standard dimensions, pixel normalization [0, 1] | `plantcare_streamlit/ml_engine.py`<br>(`prepare_image`, `LANCZOS`) | Resamples input images to 224x224 RGB float32 arrays and scales pixels by `/ 255.0`. |
| **Module 3: Dataset Ingestion** | Folder structure for healthy & diseased classes | `dataset/train/` & `dataset/test/`<br>(8 classes) | Authentic PlantVillage photos (200 train, 80 test images) with zero synthetic duplicates. |
| **Module 4: ML Architecture** | Deep learning model learning foliage patterns | `models/plant_disease_model.keras`<br>`scripts/setup_and_train.py` | MobileNetV2 backbone pre-trained on ImageNet-1K with custom Dense classification head. |
| **Module 5: Disease Detection** | Inference computing Softmax probabilities | `plantcare_streamlit/ml_engine.py`<br>(`predict_image`) | Softmax probability distribution over 8 classes, extracting top diagnosis and confidence. |
| **Module 6: Disease Advisory** | Symptom descriptions, prevention & treatments | `server/catalog.json`<br>`plantcare_streamlit/result.py` | Sourced from accredited university agricultural extensions (Cornell, Penn State, UMN). |
| **Module 7: Result & Export** | Result card, session history, pathology export | `plantcare_streamlit/result.py`<br>`plantcare_streamlit/history.py` | Medical-grade diagnostic badges, session queue, and downloadable HTML pathology reports. |

> **Auditor Note on Database:** The synopsis states *"Database: SQLite (Optional) / can optionally maintain a basic record"*. PlantCare AI maintains active session history and provides downloadable HTML pathology reports, fully satisfying requirements with zero external database locking issues.

---

## 🛠️ 2. Technology Stack & Why Each Was Used

| Layer | Component | Why Used? | Codebase File |
| :--- | :--- | :--- | :--- |
| **Language** | Python 3.10+ | Industry standard for machine learning and computer vision. | Entire Project |
| **Deep Learning** | TensorFlow 2.x & Keras (MobileNetV2) | Uses Depthwise Separable Convolutions reducing parameters to 3.4M (~20 MB), running in &lt;50ms on CPU without GPUs. | `models/plant_disease_model.keras` |
| **Frontend UI** | Streamlit 1.35+ | Pure Python reactive web framework; zero Node/npm build complexity, shared memory with ML tensors. | `streamlit_app.py`, `plantcare_streamlit/` |
| **Image Processing** | Pillow (PIL) & NumPy | High-speed LANCZOS 224x224 bicubic resampling and float32 array transformations. | `plantcare_streamlit/ml_engine.py` |
| **Knowledge Base** | Curated JSON Catalog | Verified organic care and prevention guidelines decoupled from ML code. | `server/catalog.json` |
| **Portability** | `RUN_PLANTCARE.bat` | Universal launcher using `python -m streamlit run streamlit_app.py` to prevent broken `.venv` path locks. | `RUN_PLANTCARE.bat` |

---

## 🌿 3. The 8 Trained Botanical Classes

1. **`Apple___Apple_scab`** (*Venturia inaequalis* - Fungal)
   - *Symptoms:* Olive-green to dark brown velvety circular lesions, leaf puckering.
   - *Organic Care:* Prune infected leaves, spray sulfur or potassium bicarbonate bio-fungicide.
   - *Prevention:* Plant resistant varieties, maintain open tree canopies for air circulation.
2. **`Corn___Common_rust`** (*Puccinia sorghi* - Fungal)
   - *Symptoms:* Powdery cinnamon-brown to golden-yellow pustules on upper and lower leaf surfaces.
   - *Organic Care:* Spray copper hydroxide or elemental sulfur; rogue heavily infected stalks.
   - *Prevention:* Plant rust-resistant hybrids; practice crop rotation with non-cereal crops.
3. **`Potato___Early_blight`** (*Alternaria solani* - Fungal)
   - *Symptoms:* Concentric target-board rings with yellow chlorotic margins on older bottom leaves.
   - *Organic Care:* Prune bottom leaves, spray cold-pressed neem oil (0.5%) or copper fungicide.
   - *Prevention:* 3-inch organic straw mulch, drip irrigation at base, 3-year crop rotation.
4. **`Potato___Late_blight`** (*Phytophthora infestans* - Oomycete)
   - *Symptoms:* Rapidly expanding dark water-soaked greasy lesions, white mold fuzz on leaf underside.
   - *Organic Care:* Immediate removal and disposal (never compost!), spray copper oxychloride.
   - *Prevention:* Plant certified disease-free tubers, avoid planting near tomatoes.
5. **`Potato___healthy`** (*Solanum tuberosum*)
   - *Symptoms:* Uniform rich green foliage, firm leaf blades, absence of spots or necrosis.
   - *Routine Care:* Balanced N-P-K fertilization, regular root watering.
6. **`Tomato___Early_blight`** (*Alternaria solani* - Fungal)
   - *Symptoms:* Characteristic bulls-eye target pattern of concentric brown rings with yellow halo.
   - *Organic Care:* Prune lower foliage up to 12 inches from ground, spray neem oil or bio-copper.
   - *Prevention:* Trellis and stake plants, apply straw mulch, avoid overhead watering.
7. **`Tomato___Late_blight`** (*Phytophthora infestans* - Oomycete)
   - *Symptoms:* Water-soaked pale-green to dark brown patches, white fungal growth in humid weather.
   - *Organic Care:* Immediate bag-and-destroy disposal of infected foliage, spray fixed copper.
   - *Prevention:* Wide 36-inch plant spacing, drip irrigation, plant resistant cultivars.
8. **`Tomato___healthy`** (*Solanum lycopersicum*)
   - *Symptoms:* Vibrant green foliage, smooth serrated margins, clean trichome hairs.
   - *Routine Care:* Consistent watering, organic compost mulching, regular scouting.

---

## 💻 4. Step-by-Step Installation Guide (For Friend's / Lab PC)

### Step 1: Install Python
- Download **Python 3.10, 3.11, or 3.12** from [python.org](https://www.python.org).
- **CRITICAL:** Check the box **"Add Python to PATH"** during setup!

### Step 2: Copy Project
- Copy `PlantCareAi` folder to PenDrive.
- **Do NOT copy `backend/.venv`** (it has hardcoded paths from the original PC).

### Step 3: Install Packages
Open Command Prompt inside the folder and run:
```bash
pip install -r requirements.txt
```

### Step 4: Verify Everything
Run the automated diagnostic check:
```bash
python check_environment.py
```
*(All 7 libraries and model files should show `[PASS] [OK]`!)*

### Step 5: Launch App
Simply double-click **`RUN_PLANTCARE.bat`**!  
The app opens automatically in your browser at `http://localhost:8501`.

---

## 🎯 5. Top Viva Voce Questions & Answers (Master Cheat Sheet)

1. **Q: Why choose MobileNetV2 over ResNet-50 or VGG-16?**  
   *A: ResNet-50 has 25.6M parameters and VGG-16 has 138M, requiring heavy GPUs. MobileNetV2 uses Depthwise Separable Convolutions with only 3.4M parameters (~20 MB), executing in under 50ms on standard laptop CPUs.*

2. **Q: How does Depthwise Separable Convolution work?**  
   *A: It splits standard convolution into a 3x3 depthwise convolution (spatial filtering per channel) and a 1x1 pointwise convolution (combining channels), reducing computation by 8x to 9x.*

3. **Q: What is Transfer Learning?**  
   *A: Reusing weights pre-trained on ImageNet-1K as a feature extractor and training only the custom Dense classification head on domain-specific plant images.*

4. **Q: What is the purpose of the Softmax function?**  
   *A: It normalizes raw model logits into a probability distribution summing to 1.0 (100%), allowing confident top-1 classification.*

5. **Q: How does the model distinguish Early Blight from Late Blight?**  
   *A: Early Blight (Alternaria solani) has small circular spots with concentric target rings and yellow halos. Late Blight (Phytophthora infestans) produces rapidly expanding water-soaked irregular dark lesions with white mold on the underside.*

6. **Q: What techniques prevented overfitting?**  
   *A: Data augmentation (flips, rotations, zoom), Dropout (0.3), Batch Normalization, and strictly isolated validation test splits.*

7. **Q: What happens if someone uploads a picture of a chair or human face?**  
   *A: Our calibrated decision policy checks the Softmax confidence score. If the maximum probability across all 8 classes is below the threshold, it flags the image as ambiguous/non-leaf.*

8. **Q: What was the final accuracy achieved?**  
   *A: 81.25% validation accuracy on authentic PlantVillage benchmark field photos.*

9. **Q: Can the app work without internet?**  
   *A: Yes, 100%! The trained `.keras` model, Streamlit UI, Pillow processing, and botanical catalog all run locally on the CPU.*

10. **Q: How does this help a farmer beyond just showing a class name?**  
    *A: It provides actionable visible symptoms to confirm in the field, immediate organic bio-remedies (neem oil, pruning), and long-term cultural prevention steps (crop rotation, mulch).*

---

## 🚀 6. The 3-Minute Live Viva Demo Script

- **Minute 1:** Double-click `RUN_PLANTCARE.bat` -> Explain: *"PlantCare AI runs 100% offline on CPU using MobileNetV2."*
- **Minute 2:** Upload `dataset/test/Tomato___Early_blight/test_leaf_001.jpg` -> Show predicted class **Tomato Early Blight**, the concentric target rings symptom card, and organic neem treatment.
- **Minute 3:** Upload `dataset/test/Tomato___healthy/test_leaf_001.jpg` -> Show green **Healthy Foliage** card, then click **"Download Pathology Report"** to show the generated HTML report!
- **Closing:** *"PlantCare AI bridges the gap between deep learning and practical agriculture, meeting every college synopsis requirement."*
