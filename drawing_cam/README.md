# 🎨 GDG ENSAF DRAWING CAM (AR Air & Touch Drawing)

> An interactive AR camera drawing game for **Google Developer Groups (GDG) on Campus ENSA Fez**, running entirely on your local PC hotspot or Wi-Fi network.

---

## ✨ Features & How It Works

1. **🎨 Google 4-Color Palette**:
   - Choose between official Google brand colors:
     - 🔵 **Google Blue** (`#4285F4`)
     - 🔴 **Google Red** (`#EA4335`)
     - 🟡 **Google Yellow** (`#FBBC05`)
     - 🟢 **Google Green** (`#34A853`)
   - Includes **Eraser**, **Brush Size Toggle** (Small / Medium / Large), and **Undo / Clear All**.

2. **👆 Finger Air Drawing & Mobile Screen Touch**:
   - **Screen Touch Drawing**: Drag your finger directly across your phone screen with buttery-smooth 60FPS Bézier curve interpolation.
   - **In-the-Air Hand Drawing**: Point your index finger in the camera lens to draw in mid-air using MediaPipe Hands! Pinch your thumb and index finger together to lift the pen and move without drawing.

3. **&lt; &gt; GDG Logo Stencil Guide**:
   - Tap the **`&lt; &gt;`** tool icon to toggle a faint, centered guide stencil of the Google Developer Groups bracket logo.
   - Trace the `< >` brackets with your finger to draw the official GDG symbol!

4. **📸 Selfie Snap with Official GDG ENSAF Watermark**:
   - Tap the shutter button to take a photo combining your live camera selfie + your colorful hand-drawn artwork!
   - Stamped with the official **GDG ENSAF** logo, chapter title (*"Google Developer Groups On Campus • ENSA Fez"*), `@gdg.ensaf`, and date.

5. **📱 Direct Share to Instagram Story & Tagging**:
   - Tap **"Share to Instagram Story"**:
     - Automatically copies `@gdg.ensaf` to your device clipboard.
     - Opens the native mobile share sheet directly into **Instagram Stories**!
     - Paste `@gdg.ensaf` into your Story to tag the chapter!
   - Tap **"Save to Phone"** to download directly to your mobile photo gallery.
   - Quick direct link to [Instagram @gdg.ensaf](https://www.instagram.com/gdg.ensaf/).

6. **🔒 100% Offline Local HTTPS Hotspot Server**:
   - Runs independently on port **`8445`** (can run at the same time as `puzzle_cam` on `8443`).
   - Self-generates local SSL certificates (`cert.pem` & `key.pem`) on startup.
   - Displays an ASCII QR code in the PC terminal so mobile users can scan and connect instantly.
   - Bundles all MediaPipe WebAssembly and AI models in `vendor/mediapipe/`—zero external internet required.

---

## 🚀 Quick Start Guide

### 1. Environment Setup (Virtual Environment `venv`)
Open PowerShell or Command Prompt:

```powershell
# 1. Navigate to drawing_cam directory
cd c:\1Project\gdg\projects\drawing_cam

# 2. Activate the virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt - CMD):
# venv\Scripts\activate.bat

# 3. Install dependencies inside the virtual environment
pip install -r requirements.txt
```

---

### 2. Windows Mobile Hotspot Setup (Point d'accès PC)
1. Open **Windows Settings** (`Win + I`).
2. Go to **Network & Internet** → **Mobile Hotspot**.
3. Toggle Mobile Hotspot to **On** (Share my connection over: Wi-Fi).
4. Connect your smartphone (iPhone or Android) to this Wi-Fi hotspot.

---

### 3. Launch the Server
In PowerShell with the `venv` activated:
```powershell
python server.py
```

The server will:
1. Automatically generate `cert.pem` and `key.pem`.
2. Detect your hotspot IP (e.g. `192.168.137.1`).
3. Display the exact HTTPS URL:
   ```
   https://192.168.137.1:8445/
   ```
4. Print an ASCII QR code in the terminal.

---

### 4. Open on Smartphone & SSL Bypass
1. Scan the terminal QR code or open `https://<PC-HOTSPOT-IP>:8445/` in Chrome, Safari, or Brave.
2. **Bypass the Self-Signed Certificate Warning**:
   - **Android (Chrome / Brave)**: Tap **"Advanced"** → Tap **"Proceed to 192.168.x.x (unsafe)"**.
   - **iPhone (Safari)**: Tap **"Show Details"** → Tap **"visit this website"** → Tap **"Visit Website"**.
3. **Grant Camera Permission**:
   Tap **"Allow"** when prompted for camera access.
4. Tap **"TAP TO ACTIVATE CAMERA"**, pick your Google colors, and start drawing!

---

## 🛠️ Project Structure

```
c:/1Project/gdg/projects/
├── puzzle_cam/               # 🧩 PUZZLE-CAM project (port 8443)
└── drawing_cam/              # 🎨 GDG DRAWING CAM project (port 8445)
    ├── server.py             # Python HTTPS server (default port 8445) & QR generator
    ├── index.html            # Responsive mobile UI, color palette & share sheet
    ├── app.js                # Air finger tracking, touch drawing, GDG stencil & Instagram share
    ├── style.css             # Google 4-color ambient aesthetic & glassmorphism
    ├── logo.png              # Official GDG ENSAF transparent logo
    ├── requirements.txt      # Python dependencies (cryptography, qrcode, Pillow)
    ├── test_server.py        # Automated test suite
    ├── .gitignore            # Ignores venv/, certs, and cache
    ├── venv/                 # Isolated Python virtual environment
    ├── vendor/               # Bundled MediaPipe assets for 100% offline hotspot support
    │   └── mediapipe/
    │       ├── camera_utils.js
    │       ├── drawing_utils.js
    │       ├── hands.js
    │       ├── hands.binarypb
    │       ├── hands_solution_wasm_bin.wasm
    │       └── ...
    └── README.md             # Documentation & instructions
```

---

## 💡 Controls Guide

| Tool | Action | Description |
| :--- | :--- | :--- |
| **🔵🔴🟡🟢 Colors** | **Palette** | Switch between Google Blue, Red, Yellow, Green. |
| **🧼 Eraser** | **Erase** | Erase specific lines or strokes. |
| **⚫ Brush Size** | **Thickness** | Toggle between Small (5px), Medium (10px), Large (18px). |
| **&lt; &gt; Stencil** | **Template** | Toggle faint GDG `< >` bracket stencil guide on screen. |
| **↩️ Undo / 🗑️ Clear** | **Manage** | Undo last stroke or clear all drawings. |
| **📸 Shutter** | **Capture** | Take photo with selfie + drawing + GDG ENSAF watermark. |
| **📲 Instagram** | **Share Story** | Copies `@gdg.ensaf` to clipboard and opens Instagram Stories. |

