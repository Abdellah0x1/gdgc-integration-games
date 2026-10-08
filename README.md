# GDG on Campus ENSAF — Integration Games

A suite of interactive, mobile-optimized Computer Vision and 3D web games built for **Google Developer Groups on Campus ENSA Fès** integration days and tech booths.

![GDG ENSAF Logo](logo.png)

---

## 🎮 The Games

### 1. 🧩 [Puzzle Cam](./puzzle_cam/)
- **Technology**: MediaPipe FaceMesh & Hands, HTML5 Canvas, WebRTC.
- **Gameplay**:
  - Bring both hands together in a frame OR close both eyes to trigger a 3-second camera countdown.
  - The captured image is divided into a 3x3 jigsaw puzzle.
  - Pinch thumb and index finger to freely drag and assemble puzzle chunks.
  - Exports completed photo with official GDG ENSAF branding directly to mobile device.

### 2. 🎨 [AR Finger Drawing](./drawing_cam/)
- **Technology**: MediaPipe Hands Gesture Tracking, WebRTC, HTML5 Canvas.
- **Gameplay**:
  - Air-draw in real time using your index finger.
  - Switch between official Google developer colors (Red, Blue, Yellow, Green).
  - Guide stencil for drawing the GDG ENSAF logo.
  - Direct 1-tap Instagram Story sharing with automatic `@gdg.ensaf` mention copying.

### 3. 🎲 [Rubik's Cube Solver 3D](./rubiks_solver/)
- **Technology**: Herbert Kociemba Two-Phase Algorithm (`min2phase.js`), CSS 3D Transforms, WebRTC.
- **Gameplay**:
  - Scan all 6 faces using mobile camera with 3x3 alignment reticle and HSV color classification.
  - Interactive 2D unfolded cross net for manual color corrections.
  - Real-time 3D animated cube turning guide with directional arrows and step-by-step move badges.

---

## 🚀 Live Cloud Deployment (100% Free)

All 3 games are pure client-side web applications running entirely inside modern mobile and desktop browsers with zero server maintenance required.

### Deploy with Firebase Hosting
```bash
# 1. Install & Login
npm install -g firebase-tools
firebase login

# 2. Deploy
firebase deploy --only hosting
```

### Deploy with Vercel
1. Push this repository to GitHub: `https://github.com/gdgoc-ensaf/integration-games.git`
2. Connect your GitHub repository to [vercel.com](https://vercel.com)
3. Instant automatic HTTPS URL with zero configuration.

### Deploy with GitHub Pages
1. Go to repository **Settings** -> **Pages**.
2. Select **Branch: main**, **Folder: / (root)**.
3. Save.

---

## 💻 Local Testing
To test locally using Node.js:
```bash
npx serve .
```
Or with Python:
```bash
python -m http.server 8080
```

---

## 👥 Community
Developed by **Google Developer Groups on Campus — ENSA Fès**.  
- Instagram: [@gdg.ensaf](https://www.instagram.com/gdg.ensaf/)
