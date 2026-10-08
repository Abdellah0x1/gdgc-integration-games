// GDG ENSAF Rubik's Cube Solver 3D — Main Controller
(function() {
  'use strict';

  // Standard Western Color Scheme & Mapping
  // Center 4 is the fixed anchor for each face
  const COLOR_NAMES = {
    'W': 'White',
    'Y': 'Yellow',
    'G': 'Green',
    'B': 'Blue',
    'R': 'Red',
    'O': 'Orange'
  };

  const DEFAULT_CENTERS = {
    'U': 'W', // Up = White
    'L': 'O', // Left = Orange
    'F': 'G', // Front = Green
    'R': 'R', // Right = Red
    'B': 'B', // Back = Blue
    'D': 'Y'  // Down = Yellow
  };

  // State: 6 faces x 9 stickers
  let cubeState = {
    'U': Array(9).fill('W'),
    'L': Array(9).fill('O'),
    'F': Array(9).fill('G'),
    'R': Array(9).fill('R'),
    'B': Array(9).fill('B'),
    'D': Array(9).fill('Y')
  };

  let selectedPaletteColor = 'W';
  let solutionMoves = [];
  let currentMoveIndex = 0;
  let isAutoPlaying = false;
  let autoPlayTimer = null;

  // Camera State
  let cameraStream = null;
  const SCAN_ORDER = ['F', 'R', 'B', 'L', 'U', 'D'];
  const SCAN_INFO = {
    'F': { name: 'Front (Green)', hint: 'Hold cube with Green in front and White on top.' },
    'R': { name: 'Right (Red)', hint: 'Turn cube left 90°: Red in front, White on top.' },
    'B': { name: 'Back (Blue)', hint: 'Turn cube left 90°: Blue in front, White on top.' },
    'L': { name: 'Left (Orange)', hint: 'Turn cube left 90°: Orange in front, White on top.' },
    'U': { name: 'Up (White)', hint: 'Tilt cube down: White in front, Blue on top.' },
    'D': { name: 'Down (Yellow)', hint: 'Tilt cube up: Yellow in front, Green on top.' }
  };
  let scanStep = 0;

  // DOM Elements
  const tabs = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');
  const paletteChips = document.querySelectorAll('.palette-chip');
  const btnReset = document.getElementById('btn-reset-cube');
  const btnScramble = document.getElementById('btn-scramble-cube');
  const btnSolve = document.getElementById('btn-solve-now');
  const statusValidation = document.getElementById('status-validation');

  const cube3dRoot = document.getElementById('cube-3d-root');
  const moveBadge = document.getElementById('current-move-badge');
  const moveName = document.getElementById('current-move-name');
  const moveDesc = document.getElementById('current-move-desc');
  const btnPrev = document.getElementById('btn-prev-move');
  const btnPlay = document.getElementById('btn-play-pause');
  const btnNext = document.getElementById('btn-next-move');
  const btnResetPlay = document.getElementById('btn-reset-playback');
  const progressFill = document.getElementById('solution-progress');
  const stepCurNum = document.getElementById('current-step-num');
  const stepTotNum = document.getElementById('total-step-num');
  const ribbonContainer = document.getElementById('moves-ribbon');

  // Camera DOM
  const btnToggleCam = document.getElementById('btn-toggle-cam');
  const btnCaptureFace = document.getElementById('btn-capture-face');
  const videoElem = document.getElementById('camera-video');
  const canvasElem = document.getElementById('camera-canvas');
  const scanStepIdx = document.getElementById('scan-step-idx');
  const scanStepName = document.getElementById('scan-step-name');
  const scanStepHint = document.getElementById('scan-step-hint');

  // Initialize
  function init() {
    setupTabs();
    setupPalette();
    renderNet();
    updateColorCounts();
    setupNetActions();
    setupSolutionControls();
    setupCamera();
    render3DCube();
  }

  // Tabs Switching
  function setupTabs() {
    tabs.forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.getAttribute('data-tab');
        tabs.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(target).classList.add('active');
      });
    });
  }

  // Palette Selection
  function setupPalette() {
    paletteChips.forEach(chip => {
      chip.addEventListener('click', () => {
        paletteChips.forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        selectedPaletteColor = chip.getAttribute('data-color');
      });
    });
  }

  // Render 2D Net
  function renderNet() {
    ['U', 'L', 'F', 'R', 'B', 'D'].forEach(face => {
      const container = document.getElementById(`grid-${face}`);
      if (!container) return;
      container.innerHTML = '';
      for (let i = 0; i < 9; i++) {
        const sticker = document.createElement('div');
        sticker.className = `sticker color-${cubeState[face][i]}`;
        if (i === 4) sticker.classList.add('center-sticker');
        sticker.dataset.face = face;
        sticker.dataset.index = i;

        sticker.addEventListener('click', () => {
          cubeState[face][i] = selectedPaletteColor;
          sticker.className = `sticker color-${selectedPaletteColor}${i === 4 ? ' center-sticker' : ''}`;
          updateColorCounts();
          render3DCube();
        });

        container.appendChild(sticker);
      }
    });
  }

  // Update Color Counts & Validation
  function updateColorCounts() {
    const counts = { 'W': 0, 'Y': 0, 'G': 0, 'B': 0, 'R': 0, 'O': 0 };
    Object.values(cubeState).forEach(face => {
      face.forEach(col => { if (counts[col] !== undefined) counts[col]++; });
    });

    let allNine = true;
    Object.entries(counts).forEach(([col, cnt]) => {
      const el = document.getElementById(`count-${col}`);
      if (el) {
        el.textContent = cnt;
        el.style.color = cnt === 9 ? 'var(--gdg-green)' : 'var(--gdg-red)';
      }
      if (cnt !== 9) allNine = false;
    });

    if (allNine) {
      statusValidation.className = 'status-msg success';
      statusValidation.textContent = '✓ Cube is balanced (9 stickers of each color). Ready to solve!';
    } else {
      statusValidation.className = 'status-msg';
      statusValidation.textContent = '';
    }
  }

  // Reset to Solved State
  function resetSolved() {
    cubeState = {
      'U': Array(9).fill('W'),
      'L': Array(9).fill('O'),
      'F': Array(9).fill('G'),
      'R': Array(9).fill('R'),
      'B': Array(9).fill('B'),
      'D': Array(9).fill('Y')
    };
    renderNet();
    updateColorCounts();
    render3DCube();
  }

  // Generate Random Scramble
  function generateScramble() {
    if (window.min2phase && typeof window.min2phase.randomCube === 'function') {
      const facelet = window.min2phase.randomCube();
      parseFaceletToState(facelet);
    } else {
      // Fallback: apply 20 random moves
      resetSolved();
      const moves = ['U', "U'", 'U2', 'D', "D'", 'D2', 'L', "L'", 'L2', 'R', "R'", 'R2', 'F', "F'", 'F2', 'B', "B'", 'B2'];
      let prev = '';
      for (let i = 0; i < 22; i++) {
        let m = moves[Math.floor(Math.random() * moves.length)];
        while (m[0] === prev) m = moves[Math.floor(Math.random() * moves.length)];
        prev = m[0];
        applyMoveToState(m);
      }
    }
    renderNet();
    updateColorCounts();
    render3DCube();
  }

  // Parse Kociemba 54-char string into state
  // Kociemba standard: U1..U9, R1..R9, F1..F9, D1..D9, L1..L9, B1..B9
  function parseFaceletToState(facelet) {
    if (facelet.length !== 54) return;
    const mapping = {
      'U': cubeState.U[4] || 'W',
      'R': cubeState.R[4] || 'R',
      'F': cubeState.F[4] || 'G',
      'D': cubeState.D[4] || 'Y',
      'L': cubeState.L[4] || 'O',
      'B': cubeState.B[4] || 'B'
    };

    const getFaceCol = (faceChar) => mapping[faceChar] || 'W';

    for (let i = 0; i < 9; i++) cubeState.U[i] = getFaceCol(facelet[i]);
    for (let i = 0; i < 9; i++) cubeState.R[i] = getFaceCol(facelet[9 + i]);
    for (let i = 0; i < 9; i++) cubeState.F[i] = getFaceCol(facelet[18 + i]);
    for (let i = 0; i < 9; i++) cubeState.D[i] = getFaceCol(facelet[27 + i]);
    for (let i = 0; i < 9; i++) cubeState.L[i] = getFaceCol(facelet[36 + i]);
    for (let i = 0; i < 9; i++) cubeState.B[i] = getFaceCol(facelet[45 + i]);
  }

  // Convert current state into Kociemba Facelet String
  function getStateToFacelet() {
    const centerToFace = {};
    centerToFace[cubeState.U[4]] = 'U';
    centerToFace[cubeState.R[4]] = 'R';
    centerToFace[cubeState.F[4]] = 'F';
    centerToFace[cubeState.D[4]] = 'D';
    centerToFace[cubeState.L[4]] = 'L';
    centerToFace[cubeState.B[4]] = 'B';

    if (Object.keys(centerToFace).length !== 6) {
      throw new Error('All 6 center stickers must have unique colors!');
    }

    let str = '';
    cubeState.U.forEach(c => str += (centerToFace[c] || ''));
    cubeState.R.forEach(c => str += (centerToFace[c] || ''));
    cubeState.F.forEach(c => str += (centerToFace[c] || ''));
    cubeState.D.forEach(c => str += (centerToFace[c] || ''));
    cubeState.L.forEach(c => str += (centerToFace[c] || ''));
    cubeState.B.forEach(c => str += (centerToFace[c] || ''));

    if (str.length !== 54) {
      throw new Error('Unknown sticker color found. Please verify all 54 stickers.');
    }
    return str;
  }

  // Solve Cube
  function solveCube() {
    try {
      statusValidation.className = 'status-msg';
      statusValidation.textContent = '';

      const facelet = getStateToFacelet();
      let solutionRaw = '';

      if (window.min2phase && typeof window.min2phase.solve === 'function') {
        solutionRaw = window.min2phase.solve(facelet);
      } else {
        throw new Error('Solver engine is still initializing. Please wait a second.');
      }

      if (!solutionRaw || solutionRaw.trim() === '') {
        statusValidation.className = 'status-msg success';
        statusValidation.textContent = '🎉 Cube is already completely solved!';
        return;
      }

      solutionMoves = solutionRaw.trim().split(/\s+/).filter(m => m.length > 0);
      currentMoveIndex = 0;

      // Switch to solution tab
      document.querySelector('[data-tab="tab-solution"]').click();
      renderSolutionUI();

    } catch (err) {
      statusValidation.className = 'status-msg error';
      statusValidation.textContent = `❌ ${err.message}`;
    }
  }

  // Move Descriptions & Details
  function getMoveDetails(move) {
    const faceMap = {
      'R': 'Right (Red)',
      'L': 'Left (Orange)',
      'U': 'Up (White)',
      'D': 'Down (Yellow)',
      'F': 'Front (Green)',
      'B': 'Back (Blue)'
    };
    const f = move[0];
    const mod = move.slice(1);
    const fname = faceMap[f] || f;

    if (mod === "'") {
      return {
        name: `Turn ${fname} Counter-Clockwise`,
        desc: `Rotate the ${fname} layer 90° counter-clockwise (anticlockwise).`
      };
    } else if (mod === '2') {
      return {
        name: `Turn ${fname} 180° (Half Turn)`,
        desc: `Rotate the ${fname} layer a full 180° (two quarter turns).`
      };
    } else {
      return {
        name: `Turn ${fname} Clockwise`,
        desc: `Rotate the ${fname} layer 90° clockwise.`
      };
    }
  }

  // Render Solution UI
  function renderSolutionUI() {
    stepTotNum.textContent = solutionMoves.length;
    stepCurNum.textContent = currentMoveIndex;
    progressFill.style.width = `${(currentMoveIndex / solutionMoves.length) * 100}%`;

    btnPrev.disabled = currentMoveIndex === 0;
    btnNext.disabled = currentMoveIndex >= solutionMoves.length;
    btnPlay.disabled = solutionMoves.length === 0;

    // Render Ribbon
    ribbonContainer.innerHTML = '';
    solutionMoves.forEach((m, idx) => {
      const el = document.createElement('div');
      el.className = `ribbon-move${idx === currentMoveIndex ? ' active' : ''}${idx < currentMoveIndex ? ' done' : ''}`;
      el.textContent = m;
      el.addEventListener('click', () => {
        currentMoveIndex = idx;
        renderSolutionUI();
      });
      ribbonContainer.appendChild(el);
    });

    if (currentMoveIndex < solutionMoves.length) {
      const curMove = solutionMoves[currentMoveIndex];
      moveBadge.textContent = curMove;
      const details = getMoveDetails(curMove);
      moveName.textContent = details.name;
      moveDesc.textContent = details.desc;
    } else {
      moveBadge.textContent = '🎉';
      moveName.textContent = 'Cube Solved!';
      moveDesc.textContent = 'All moves completed successfully!';
      if (isAutoPlaying) toggleAutoPlay();
    }
  }

  // Next / Prev Move Actions
  function nextMove() {
    if (currentMoveIndex < solutionMoves.length) {
      applyMoveToState(solutionMoves[currentMoveIndex]);
      currentMoveIndex++;
      render3DCube();
      renderNet();
      renderSolutionUI();
    }
  }

  function prevMove() {
    if (currentMoveIndex > 0) {
      currentMoveIndex--;
      const m = solutionMoves[currentMoveIndex];
      const invMove = invertMove(m);
      applyMoveToState(invMove);
      render3DCube();
      renderNet();
      renderSolutionUI();
    }
  }

  function invertMove(m) {
    if (m.endsWith('2')) return m;
    if (m.endsWith("'")) return m[0];
    return m + "'";
  }

  function toggleAutoPlay() {
    isAutoPlaying = !isAutoPlaying;
    if (isAutoPlaying) {
      btnPlay.textContent = '⏸ Pause';
      autoPlayTimer = setInterval(() => {
        if (currentMoveIndex < solutionMoves.length) {
          nextMove();
        } else {
          toggleAutoPlay();
        }
      }, 1400);
    } else {
      btnPlay.textContent = '▶ Auto Play';
      clearInterval(autoPlayTimer);
      autoPlayTimer = null;
    }
  }

  function resetPlayback() {
    if (isAutoPlaying) toggleAutoPlay();
    currentMoveIndex = 0;
    renderSolutionUI();
  }

  // Cube Rotations Math (Simulate standard moves on 54-sticker state)
  function rotateFaceClockwise(face) {
    const old = [...cubeState[face]];
    cubeState[face][0] = old[6]; cubeState[face][1] = old[3]; cubeState[face][2] = old[0];
    cubeState[face][3] = old[7]; cubeState[face][4] = old[4]; cubeState[face][5] = old[1];
    cubeState[face][6] = old[8]; cubeState[face][7] = old[5]; cubeState[face][8] = old[2];
  }

  function applyMoveToState(move) {
    const f = move[0];
    const mod = move.slice(1);
    const times = mod === '2' ? 2 : mod === "'" ? 3 : 1;

    for (let t = 0; t < times; t++) {
      rotateFaceClockwise(f);
      if (f === 'U') {
        const temp = [cubeState.F[0], cubeState.F[1], cubeState.F[2]];
        cubeState.F[0] = cubeState.R[0]; cubeState.F[1] = cubeState.R[1]; cubeState.F[2] = cubeState.R[2];
        cubeState.R[0] = cubeState.B[0]; cubeState.R[1] = cubeState.B[1]; cubeState.R[2] = cubeState.B[2];
        cubeState.B[0] = cubeState.L[0]; cubeState.B[1] = cubeState.L[1]; cubeState.B[2] = cubeState.L[2];
        cubeState.L[0] = temp[0]; cubeState.L[1] = temp[1]; cubeState.L[2] = temp[2];
      } else if (f === 'D') {
        const temp = [cubeState.F[6], cubeState.F[7], cubeState.F[8]];
        cubeState.F[6] = cubeState.L[6]; cubeState.F[7] = cubeState.L[7]; cubeState.F[8] = cubeState.L[8];
        cubeState.L[6] = cubeState.B[6]; cubeState.L[7] = cubeState.B[7]; cubeState.L[8] = cubeState.B[8];
        cubeState.B[6] = cubeState.R[6]; cubeState.B[7] = cubeState.R[7]; cubeState.B[8] = cubeState.R[8];
        cubeState.R[6] = temp[0]; cubeState.R[7] = temp[1]; cubeState.R[8] = temp[2];
      } else if (f === 'R') {
        const temp = [cubeState.U[2], cubeState.U[5], cubeState.U[8]];
        cubeState.U[2] = cubeState.F[2]; cubeState.U[5] = cubeState.F[5]; cubeState.U[8] = cubeState.F[8];
        cubeState.F[2] = cubeState.D[2]; cubeState.F[5] = cubeState.D[5]; cubeState.F[8] = cubeState.D[8];
        cubeState.D[2] = cubeState.B[6]; cubeState.D[5] = cubeState.B[3]; cubeState.D[8] = cubeState.B[0];
        cubeState.B[6] = temp[0]; cubeState.B[3] = temp[1]; cubeState.B[0] = temp[2];
      } else if (f === 'L') {
        const temp = [cubeState.U[0], cubeState.U[3], cubeState.U[6]];
        cubeState.U[0] = cubeState.B[8]; cubeState.U[3] = cubeState.B[5]; cubeState.U[6] = cubeState.B[2];
        cubeState.B[8] = cubeState.D[0]; cubeState.B[5] = cubeState.D[3]; cubeState.B[2] = cubeState.D[6];
        cubeState.D[0] = cubeState.F[0]; cubeState.D[3] = cubeState.F[3]; cubeState.D[6] = cubeState.F[6];
        cubeState.F[0] = temp[0]; cubeState.F[3] = temp[1]; cubeState.F[6] = temp[2];
      } else if (f === 'F') {
        const temp = [cubeState.U[6], cubeState.U[7], cubeState.U[8]];
        cubeState.U[6] = cubeState.L[8]; cubeState.U[7] = cubeState.L[5]; cubeState.U[8] = cubeState.L[2];
        cubeState.L[2] = cubeState.D[0]; cubeState.L[5] = cubeState.D[1]; cubeState.L[8] = cubeState.D[2];
        cubeState.D[0] = cubeState.R[6]; cubeState.D[1] = cubeState.R[3]; cubeState.D[2] = cubeState.R[0];
        cubeState.R[0] = temp[0]; cubeState.R[3] = temp[1]; cubeState.R[6] = temp[2];
      } else if (f === 'B') {
        const temp = [cubeState.U[0], cubeState.U[1], cubeState.U[2]];
        cubeState.U[0] = cubeState.R[2]; cubeState.U[1] = cubeState.R[5]; cubeState.U[2] = cubeState.R[8];
        cubeState.R[2] = cubeState.D[8]; cubeState.R[5] = cubeState.D[7]; cubeState.R[8] = cubeState.D[6];
        cubeState.D[6] = cubeState.L[0]; cubeState.D[7] = cubeState.L[3]; cubeState.D[8] = cubeState.L[6];
        cubeState.L[0] = temp[2]; cubeState.L[3] = temp[1]; cubeState.L[6] = temp[0];
      }
    }
  }

  // 3D CSS Rubik's Cube Renderer
  function render3DCube() {
    if (!cube3dRoot) return;
    cube3dRoot.innerHTML = '';

    const faces = ['f', 'b', 'r', 'l', 'u', 'd'];
    const faceKeys = ['F', 'B', 'R', 'L', 'U', 'D'];

    faces.forEach((f, idx) => {
      const faceKey = faceKeys[idx];
      const faceEl = document.createElement('div');
      faceEl.className = `cube-face-3d face-3d-${f}`;

      for (let i = 0; i < 9; i++) {
        const stk = document.createElement('div');
        const color = cubeState[faceKey][i];
        stk.className = `sticker-3d color-${color}`;
        faceEl.appendChild(stk);
      }
      cube3dRoot.appendChild(faceEl);
    });
  }

  // Setup Net Actions
  function setupNetActions() {
    btnReset.addEventListener('click', resetSolved);
    btnScramble.addEventListener('click', generateScramble);
    btnSolve.addEventListener('click', solveCube);
  }

  // Setup Solution Controls
  function setupSolutionControls() {
    btnNext.addEventListener('click', nextMove);
    btnPrev.addEventListener('click', prevMove);
    btnPlay.addEventListener('click', toggleAutoPlay);
    btnResetPlay.addEventListener('click', resetPlayback);
  }

  // Setup Mobile Camera Face Scanner
  function setupCamera() {
    btnToggleCam.addEventListener('click', async () => {
      if (cameraStream) {
        stopCamera();
      } else {
        await startCamera();
      }
    });

    btnCaptureFace.addEventListener('click', () => {
      captureCurrentFace();
    });
  }

  async function startCamera() {
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' }, width: { ideal: 640 }, height: { ideal: 480 } }
      });
      videoElem.srcObject = cameraStream;
      btnToggleCam.textContent = '⏹ Stop Camera';
      btnCaptureFace.disabled = false;
      scanStep = 0;
      updateScanGuide();
    } catch (err) {
      alert('Unable to access camera: ' + err.message);
    }
  }

  function stopCamera() {
    if (cameraStream) {
      cameraStream.getTracks().forEach(t => t.stop());
      cameraStream = null;
      videoElem.srcObject = null;
      btnToggleCam.textContent = '📷 Start Camera';
      btnCaptureFace.disabled = true;
    }
  }

  function updateScanGuide() {
    const curFace = SCAN_ORDER[scanStep];
    const info = SCAN_INFO[curFace];
    scanStepIdx.textContent = scanStep + 1;
    scanStepName.textContent = info.name;
    scanStepHint.textContent = info.hint;

    document.querySelectorAll('.scanned-thumb').forEach(t => t.classList.remove('active'));
    const curThumb = document.getElementById(`thumb-${curFace}`);
    if (curThumb) curThumb.classList.add('active');
  }

  // Sample colors from video frame using HTML5 Canvas & HSV
  function captureCurrentFace() {
    const curFace = SCAN_ORDER[scanStep];
    const vw = videoElem.videoWidth || 640;
    const vh = videoElem.videoHeight || 480;
    canvasElem.width = vw;
    canvasElem.height = vh;
    const ctx = canvasElem.getContext('2d');
    ctx.drawImage(videoElem, 0, 0, vw, vh);

    const size = Math.min(vw, vh) * 0.45;
    const startX = (vw - size) / 2;
    const startY = (vh - size) / 2;
    const step = size / 3;

    const detected = [];
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 3; c++) {
        const px = startX + c * step + step / 2;
        const py = startY + r * step + step / 2;
        const col = sampleAverageColor(ctx, px, py, step * 0.3);
        detected.push(col);
      }
    }

    // Set detected face
    cubeState[curFace] = detected;
    renderNet();
    updateColorCounts();
    render3DCube();

    scanStep = (scanStep + 1) % 6;
    updateScanGuide();

    if (scanStep === 0) {
      alert('All 6 faces scanned! Check the 2D Net tab to review colors.');
      document.querySelector('[data-tab="tab-net"]').click();
    }
  }

  function sampleAverageColor(ctx, cx, cy, rad) {
    const imgData = ctx.getImageData(cx - rad / 2, cy - rad / 2, rad, rad);
    const data = imgData.data;
    let r = 0, g = 0, b = 0, count = 0;
    for (let i = 0; i < data.length; i += 4) {
      r += data[i];
      g += data[i + 1];
      b += data[i + 2];
      count++;
    }
    r /= count; g /= count; b /= count;
    return classifyRGBtoCubeColor(r, g, b);
  }

  function classifyRGBtoCubeColor(r, g, b) {
    // RGB to HSV
    const max = Math.max(r, g, b) / 255;
    const min = Math.min(r, g, b) / 255;
    const d = max - min;
    let h = 0;
    const s = max === 0 ? 0 : d / max;
    const v = max;

    if (max !== min) {
      const dr = (max - r / 255) / d;
      const dg = (max - g / 255) / d;
      const db = (max - b / 255) / d;
      if (r / 255 === max) h = db - dg;
      else if (g / 255 === max) h = 2 + dr - db;
      else h = 4 + dg - dr;
      h *= 60;
      if (h < 0) h += 360;
    }

    // Thresholds
    if (s < 0.22 && v > 0.45) return 'W'; // White
    if (h >= 45 && h <= 75) return 'Y';  // Yellow
    if (h >= 75 && h <= 165) return 'G'; // Green
    if (h >= 170 && h <= 260) return 'B'; // Blue
    if (h >= 15 && h < 45) return 'O';   // Orange
    return 'R';                          // Red
  }

  // Start on DOM ready
  document.addEventListener('DOMContentLoaded', init);
})();

