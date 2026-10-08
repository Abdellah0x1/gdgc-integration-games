# GDG ENSAF — 3D Rubik's Cube Solver

An interactive, responsive 3D Rubik's Cube Solver web application built for Google Developer Groups on Campus ENSAF.

## Features
- **Pure Client-Side Kociemba Algorithm**: Powered by Herbert Kociemba's Two-Phase algorithm (`min2phase.js`), solves any cube scramble in under 20 milliseconds.
- **Mobile Camera Face Scanner**: Guided 6-face scanning with live video stream, 3x3 alignment reticle, and real-time HSV color classification.
- **Interactive 2D Cube Net**: Unfolded cross net with manual color correction palette (White, Yellow, Green, Blue, Red, Orange) and live sticker balance validation.
- **3D Step-by-Step Move Visualizer**: Realistic 3D cube model with animated layer rotations, directional turning cues, move badges (`R`, `U'`, `F2`), and auto-play controls.
- **Offline & Cloud Ready**: Zero backend required for cloud deployment (Firebase Hosting, Vercel, GitHub Pages).

## Quick Start
Open `index.html` in any modern web browser, or serve using any static web server:
```bash
npx serve .
```
Or deploy directly to Firebase Hosting:
```bash
firebase deploy --only hosting
```

