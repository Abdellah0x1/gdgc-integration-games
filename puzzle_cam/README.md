# 📸 PUZZLE-CAM (Hand-Frame Capture)

> An interactive, real-time hand-gesture camera & puzzle game web application running entirely on your local PC hotspot or Wi-Fi network. Inspired by the **PUZZLE-CAM** concept by *mishu.ksv*.

---

## ✨ Features & How It Works

1. **🤏🤏 Gesture 1 — Double Pinch (Hand Framing & Countdown Snap)**:
   - Bring both hands into camera view and pinch thumb and index finger on both hands simultaneously.
   - An interactive, glowing viewfinder box dynamically frames the region between your two pinch points.
   - Holding the frame triggers an animated **3-second countdown** (3... 2... 1...) and snaps the photo frame with a shutter sound and screen flash!

2. **🧩 Gesture 2 — 3x3 Puzzle Slicer & Interactive Board**:
   - The captured photo frame is instantly divided into a 3x3 grid of 9 puzzle pieces.
   - Pieces are scattered across the canvas.
   - Bring pieces near their target slot to **snap them into place** with rewarding chime chords, particle burst animations, and celebratory confetti upon solving the entire puzzle!

3. **🤏 Gesture 3 — Single Pinch (Drag & Drop)**:
   - Pinch thumb and index finger on **one hand** over any puzzle piece to pick it up and smoothly drag it across the screen.
   - Release the pinch near the target grid slot to lock it in place.
   - **Direct Touch Fallback**: On mobile phones, you can also tap and drag pieces with your finger directly on the screen at any time!

4. **✊ Gesture 4 — Closed Fist (Save Photo & Reset)**:
   - Form a **closed fist** with your hand and hold it for 1 second.
   - An animated golden radial meter charges up around your fist.
   - Once filled, the assembled photo is automatically saved directly to your phone (via native Mobile Share Sheet / Camera Roll or file download)!
   - The app then resets back to live camera mode so you can snap another puzzle.

5. **🔒 Local Offline HTTPS Server**:
   - Runs with zero external cloud dependencies.
   - Automatically generates a self-signed SSL certificate (`cert.pem` & `key.pem`) on startup with Subject Alternative Names (SANs) for all local network IPs and `localhost`.
   - Renders an ASCII QR code in your PC terminal for instant phone connection.
   - Bundles local MediaPipe WASM and neural network models in `vendor/mediapipe/` for 100% offline hotspot setups (no internet required).

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.9+ installed on your PC.
- Navigate to the project folder and install dependencies:
  ```powershell
  cd puzzle_cam
  pip install -r requirements.txt
  ```

---

### 2. Windows Mobile Hotspot Setup (Point d'accès PC)
To connect phones without needing an existing router or internet connection:
1. Open **Windows Settings** (`Win + I`).
2. Go to **Network & Internet** → **Mobile Hotspot**.
3. Toggle Mobile Hotspot to **On** (Share my internet connection over: Wi-Fi).
   *(Note: Hotspot works even if PC is offline)*.
4. Note your Hotspot Wi-Fi Name (SSID) and Password.
5. Connect your mobile phone (iPhone or Android) to this Wi-Fi hotspot.

---

### 3. Launch the Server
In PowerShell or Command Prompt, run:
```powershell
cd puzzle_cam
python server.py
```

The server will:
1. Automatically generate `cert.pem` and `key.pem` if not already present.
2. Detect the hotspot IP (typically `192.168.137.1` on Windows) or your local Wi-Fi IP.
3. Display the exact HTTPS URL:
   ```
   https://192.168.137.1:8443/
   ```
4. Print an ASCII QR code in the terminal.

---

### 4. Open on Smartphone & SSL Bypass
1. Scan the terminal QR code with your phone camera, or open Chrome/Safari/Brave and type the URL (e.g. `https://192.168.137.1:8443`).
2. **Bypass the Self-Signed Certificate Warning**:
   Because the SSL certificate is generated locally on your PC (so camera permissions work over HTTPS without internet), your phone browser will show a standard security prompt:
   - **On Android (Chrome / Brave)**: Tap **"Advanced"** → Tap **"Proceed to 192.168.x.x (unsafe)"**.
   - **On iPhone (Safari)**: Tap **"Show Details"** → Tap **"visit this website"** → Tap **"Visit Website"**.
3. **Grant Camera Permission**:
   Tap **"Allow"** when prompted for camera access.
4. Tap **"TAP TO ACTIVATE CAMERA"** to start the gesture detector and enjoy PUZZLE-CAM!

---

## 🕹️ Controls & HUD Guide

| UI Control | Description |
| :--- | :--- |
| **Switch Camera (🔄)** | Switch between Front Selfie camera and Rear camera. |
| **Sound Toggle (🔊)** | Toggle synthesized Web Audio sound effects. |
| **Help Guide (❓)** | View interactive gesture illustrations and rules. |
| **Shutter Button (📸)** | Manually snap a photo frame without hand gestures. |
| **Scatter (🔀)** | Re-shuffle puzzle pieces around the board. |
| **Save (💾 / ✊)** | Save the solved photo to device gallery and reset camera. |
| **Retake** | Discard puzzle and return to live camera feed. |

---

## 🛠️ Project Structure

```
c:/1Project/gdg/projects/
└── puzzle_cam/
    ├── server.py              # Python HTTPS server, auto-cert generator & QR printer
    ├── index.html             # Responsive mobile UI, HUD overlay, modals & canvas
    ├── app.js                 # MediaPipe Hands tracking, gesture logic, puzzle slicer & audio
    ├── style.css              # Cyberpunk glassmorphic responsive mobile styling
    ├── requirements.txt       # Python dependencies (cryptography, qrcode, Pillow)
    ├── test_server.py         # Automated test suite
    ├── vendor/                # Bundled MediaPipe assets for 100% offline hotspot support
    │   └── mediapipe/
    │       ├── camera_utils.js
    │       ├── drawing_utils.js
    │       ├── hands.js
    │       ├── hands.binarypb
    │       ├── hands_solution_wasm_bin.wasm
    │       ├── hand_landmark_lite.tflite
    │       └── ...
    └── README.md              # Documentation & usage instructions
```

---

## 💡 Troubleshooting & Tips

- **Camera mirror image**: When using the front selfie camera, the feed and gestures are automatically mirrored horizontally so movements feel natural.
- **Lighting**: For best hand tracking performance, ensure your hands are well-lit and held 1 to 3 feet from the camera lens.
- **Touch Drag**: If hand tracking is obscured or lighting is dim, you can drag and drop puzzle pieces directly with your finger on the smartphone screen.
- **Firewall Prompt**: If Windows Firewall asks to allow Python network access, check both "Private" and "Public" networks and click "Allow Access".
