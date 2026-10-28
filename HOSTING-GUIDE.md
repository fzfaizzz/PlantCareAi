# PlantCare AI — Run & Hosting Guide (Complete Manual)

Is guide mein local run karne ke commands aur internet par free live host karne ke step-by-step instructions diye gaye hain.

---

## 💻 1. Local Computer Par Run Kaise Karein (Exact Commands)

Aap 3 aasan tareeqon mein se kisi ek se app run kar sakte hain:

### Option A: 1-Click Batch File (Sabse Aasan)
Project folder mein humne **`run_app.bat`** file bana di hai:
1. File Explorer mein `C:\Users\akhta\Downloads\PlantCareAi` open karein.
2. **`run_app.bat`** par double click karein.
3. Command window khulegi aur browser mein automatic app open ho jayega!

---

### Option B: PowerShell Command (Recommended)
VS Code ya PowerShell terminal open karein (project root folder mein) aur yeh command run karein:

```powershell
.\backend\.venv\Scripts\streamlit.exe run streamlit_app.py
```

Ya phir venv activate karke:
```powershell
.\backend\.venv\Scripts\activate
streamlit run streamlit_app.py
```

---

### Option C: Background Mode Command
Agar aapko app background mein chalana ho:
```powershell
.\backend\.venv\Scripts\streamlit.exe run streamlit_app.py --server.headless=true --server.port=8501
```

### 🌐 App Khulne Ka URL:
Browser mein open karein:
👉 **`http://localhost:8501`**

---

## ☁️ 2. Internet Par Free Live Host Kaise Karein

Aapke college synopsis mein likha hai:
- **Language**: Python
- **Interface**: Streamlit
- **ML Engine**: TensorFlow / Keras (MobileNetV2)

Is architecture ke liye **Streamlit Community Cloud** #1 BEST aur 100% FREE platform hai.

### 🌟 Platform Comparison:

| Feature | Streamlit Community Cloud (Recommended) | Vercel |
| :--- | :--- | :--- |
| **Best For** | Python, Streamlit, TensorFlow Deep Learning | Node.js, Next.js, React Frontend |
| **Price** | 100% Free Forever | 100% Free |
| **TensorFlow ML Support** | Native Python CPU support (Full Keras model) | Serverless 250MB limit (Heavy ML fails) |
| **College Synopsis Match** | **100% Exact Match (Streamlit UI + Python)** | React UI only |
| **Deployment Time** | 2 Minutes | 2 Minutes |

---

### 🚀 Streamlit Cloud Par Deploy Karne Ke Steps (2 Minutes):

#### Step 1: Apne Code Ko GitHub Par Dalein
PowerShell mein yeh commands run karein:
```powershell
git init
git add .
git commit -m "PlantCare AI: Deep Learning model and Streamlit UI"
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/PlantCareAi.git
git push -u origin main
```
*(Note: `models/plant_disease_model.h5` sirf 11 MB ki hai, yeh GitHub par bina kisi issue ke direct upload ho jayegi).*

#### Step 2: Streamlit Cloud Par Login Karein
1. Browser mein **[share.streamlit.io](https://share.streamlit.io)** open karein.
2. Apne GitHub account se **"Sign in with GitHub"** karein.

#### Step 3: New App Create Karein
1. Right corner mein **"New app"** button click karein.
2. Select karein:
   - **Repository**: `<YOUR_USERNAME>/PlantCareAi`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
   - **App URL (optional)**: e.g., `plantcare-ai-final.streamlit.app`
3. **Advanced settings** (Optional - Gemini Cloud ke liye):
   - "Secrets" section mein likhein:
     ```toml
     GEMINI_API_KEY = "your_gemini_api_key_here"
     GEMINI_MODEL = "gemini-3.1-flash-lite"
     ```
4. Click **"Deploy"**!

#### Step 4: Live Link!
2-3 minute mein build complete ho jayegi aur aapko public live link mil jayegi:
👉 `https://plantcare-ai.streamlit.app`

Is link ko aap apne mobile par, doston ko, ya college professor ko share kar sakte hain!

---

## ⚡ 3. Vercel Par Deploy Karna (Optional React Frontend)

Agar aapko React/Vite version Vercel par host karna ho:
1. [vercel.com](https://vercel.com) par login karein.
2. **"Add New Project"** par click karein aur GitHub repo import karein.
3. Build Settings:
   - Framework: `Vite`
   - Root Directory: `./`
   - Build Command: `npm run build`
   - Output Directory: `dist`
4. Environment Variables:
   - `GEMINI_API_KEY`: Aapki gemini key
   - `GEMINI_MODEL`: `gemini-3.1-flash-lite`
5. Click **"Deploy"**.

---

## 🎓 College Viva Ke Liye Pro-Tip:
Viva ke din laptop par **`run_app.bat`** chala kar **`http://localhost:8501`** par demo dein!
- College ke WiFi ya hotspot ki zaroorat nahi padegi.
- Response 0.1 second mein aayega (zero lag).
- Examiner ke samne 100% safe aur reliable rahega.
- Aur backup ke liye phone ya tablet par Streamlit Cloud wali live link khol kar rakh sakte hain!
