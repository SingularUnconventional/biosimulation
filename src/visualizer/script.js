// === 캔버스 설정 ===
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
canvas.width = window.innerWidth;
canvas.height = window.innerHeight - 40;

// === 상수 ===
const GRID_SIZE = 300;
const ORGANIC_ENERGY_SCALE = 5000.0;
const CREATURE_RADIUS = 4;
const FRAMES_PER_FILE = 100;
const LOG_DIR = "/logs/compressed/";

// === 상태 변수 ===
let cameraX = 0, cameraY = 0, zoom = 1;
let isPlaying = true;
let isDragging = false;
let lastMouse = { x: 0, y: 0 };
let isTouching = false;
let lastTouch = [], lastDist = null;
let tapStartTime = 0;
let tapStartPos = null;
let currentFrame = 1;
let totalFrames = 0;
let parsedObjects = [];
let selectedObject = null;
let currentFileFrames = [];
let currentFileRange = { start: -1, end: -1 };
let preloadCache = {};
let preloadingFile = null;


const MAX_CACHE_FILES = 7; // 동시에 유지할 zst 블록 수
const cacheQueue = [];      // 순서 관리용

const frameCache = {};          // filename => frames[]
const fileLoadPromises = {};    // filename => Promise resolving to frames[]
const PRELOAD_LOOKAHEAD = 7;    // 미리 로드할 파일 개수

function worldToScreen(x, y) {
  return { x: (x - cameraX) * zoom, y: (y - cameraY) * zoom };
}
function screenToWorld(x, y) {
  return { x: x / zoom + cameraX, y: y / zoom + cameraY };
}

// === 마우스 이벤트 ===
canvas.addEventListener("mousedown", e => {
  isDragging = true;
  lastMouse = { x: e.clientX, y: e.clientY };
});
canvas.addEventListener("mouseup", () => isDragging = false);
canvas.addEventListener("mousemove", e => {
  if (isDragging) {
    const dx = (e.clientX - lastMouse.x) / zoom;
    const dy = (e.clientY - lastMouse.y) / zoom;
    cameraX -= dx;
    cameraY -= dy;
    lastMouse = { x: e.clientX, y: e.clientY };
  }
});
canvas.addEventListener("wheel", e => {
  const zoomFactor = 1.1;
  const oldZoom = zoom;
  zoom = e.deltaY < 0 ? zoom * zoomFactor : zoom / zoomFactor;
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  const wx = mx / oldZoom + cameraX;
  const wy = my / oldZoom + cameraY;
  cameraX = wx - mx / zoom;
  cameraY = wy - my / zoom;
  e.preventDefault();
});
canvas.addEventListener("click", e => {
  const rect = canvas.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;
  handleObjectSelection(mouseX, mouseY);
});

// === 터치 이벤트 ===
canvas.addEventListener("touchstart", e => {
  if (e.touches.length === 1) {
    isTouching = true;
    lastTouch = [{ x: e.touches[0].clientX, y: e.touches[0].clientY }];
    tapStartTime = Date.now();
    tapStartPos = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    lastDist = null;
  } else if (e.touches.length === 2) {
    lastTouch = [
      { x: e.touches[0].clientX, y: e.touches[0].clientY },
      { x: e.touches[1].clientX, y: e.touches[1].clientY }
    ];
    lastDist = Math.hypot(
      lastTouch[0].x - lastTouch[1].x,
      lastTouch[0].y - lastTouch[1].y
    );
  }
  e.preventDefault();
}, { passive: false });

canvas.addEventListener("touchmove", e => {
  if (e.touches.length === 1 && isTouching) {
    const dx = (e.touches[0].clientX - lastTouch[0].x) / zoom;
    const dy = (e.touches[0].clientY - lastTouch[0].y) / zoom;
    cameraX -= dx;
    cameraY -= dy;
    lastTouch = [{ x: e.touches[0].clientX, y: e.touches[0].clientY }];
  } else if (e.touches.length === 2) {
    const touch0 = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    const touch1 = { x: e.touches[1].clientX, y: e.touches[1].clientY };
    const dist = Math.hypot(touch0.x - touch1.x, touch0.y - touch1.y);
    if (lastDist) {
      const scale = dist / lastDist;
      const midX = (touch0.x + touch1.x) / 2;
      const midY = (touch0.y + touch1.y) / 2;
      const wx = midX / zoom + cameraX;
      const wy = midY / zoom + cameraY;
      zoom *= scale;
      cameraX = wx - midX / zoom;
      cameraY = wy - midY / zoom;
    }
    lastTouch = [touch0, touch1];
    lastDist = dist;
  }
  e.preventDefault();
}, { passive: false });

canvas.addEventListener("touchend", e => {
  isTouching = false;
  if (e.changedTouches.length === 1 && tapStartPos) {
    const touch = e.changedTouches[0];
    const dx = touch.clientX - tapStartPos.x;
    const dy = touch.clientY - tapStartPos.y;
    const duration = Date.now() - tapStartTime;
    if (Math.hypot(dx, dy) < 10 && duration < 300) {
      const rect = canvas.getBoundingClientRect();
      const x = touch.clientX - rect.left;
      const y = touch.clientY - rect.top;
      handleObjectSelection(x, y);
    }
  }
  lastTouch = [];
  lastDist = null;
});

// === 생물 선택 공통 함수 ===
function handleObjectSelection(screenX, screenY) {
  const world = screenToWorld(screenX, screenY);
  let found = null;
  for (const obj of parsedObjects) {
    const dx = obj.x - world.x;
    const dy = obj.y - world.y;
    if (Math.sqrt(dx * dx + dy * dy) < 10) {
      found = obj;
      break;
    }
  }
  selectedObject = (selectedObject && selectedObject.id === found?.id) ? null : found;
  updateInfoBox();
}

function updateInfoBox() {
  const sidebar = document.getElementById("sidebar");
  if (selectedObject) {
    const latest = parsedObjects.find(obj => obj.id === selectedObject.id);
    if (latest) {
      sidebar.innerHTML = `
        <h3>Creature #${latest.id}</h3>
        <p><strong>HP:</strong> ${latest.hp.toFixed(2)}</p>
        <p><strong>Energy:</strong> ${latest.energy.toFixed(4)}</p>
        <p><strong>Position:</strong><br>X: ${latest.x.toFixed(2)}<br>Y: ${latest.y.toFixed(2)}</p>
      `;
    } else {
      sidebar.innerHTML = `<em>Creature #${selectedObject.id} not found</em>`;
    }
  } else {
    sidebar.innerHTML = "<em>No object selected</em>";
  }
}

// === creatures 정보 추출 ===
function extractCreaturesFromTurn(turnData) {
  const creatures = [];
  for (const row of turnData.grids) {
    for (const cell of row) {
      for (const c of cell.creatures) {
        creatures.push({
          id: c.id,
          x: c.position.x,
          y: c.position.y,
          hp: c.health,
          energy: c.energy
        });
      }
    }
  }
  return creatures;
}

function findFileForFrame(frame) {
  const end = Math.ceil(frame / FRAMES_PER_FILE) * FRAMES_PER_FILE;
  const start = end - FRAMES_PER_FILE + 1;
  const filename = `turn_logs_${String(end).padStart(8, "0")}.zst`;
  return { filename, start, end };
}

function fetchAndParseFile(filename) {
  return fetch(`${LOG_DIR}${filename}`)
    .then(res => res.arrayBuffer())
    .then(buffer => {
      const decoded = new TextDecoder("utf-8").decode(buffer);
      const lines = decoded.trim().split("\n");
      if (lines.length === 0) throw new Error(`빈 로그 파일: ${filename}`);
      return lines;
    });
}

function cacheFile(filename, frames) {
  frameCache[filename] = frames;
  cacheQueue.push(filename);

  // 초과 시 가장 오래된 항목 제거
  if (cacheQueue.length > MAX_CACHE_FILES) {
    const oldest = cacheQueue.shift();
    delete frameCache[oldest];
    delete fileLoadPromises[oldest]; // (optional)
  }
}

async function loadCompressedFile(filename) {
  if (frameCache[filename]) {
    currentFileFrames = frameCache[filename];
    return;
  }

  if (!fileLoadPromises[filename]) {
    // 직접 재생 시 로드되지 않았다면 직접 시작
    fileLoadPromises[filename] = fetchAndParseFile(filename)
    .then(frames => { frameCache[filename] = frames; return frames; })
    .catch(e => {
      console.error(`❗ 파일 로딩 실패: ${filename}`, e);
      delete fileLoadPromises[filename];
      throw e;
    });
  }

  currentFileFrames = await fileLoadPromises[filename];
}

function preloadNextFiles(currentFrame) {
  for (let i = 1; i <= PRELOAD_LOOKAHEAD; i++) {
    const { filename } = findFileForFrame(currentFrame + i * FRAMES_PER_FILE);
    if (!fileLoadPromises[filename]) {
      fileLoadPromises[filename] = fetchAndParseFile(filename)
        .then(frames => { frameCache[filename] = frames; return frames; })
        .catch(e => {
          console.warn(`❗ 프리로드 실패: ${filename}`, e);
          delete fileLoadPromises[filename];
        });
    }
  }
}

async function update() {
  if (isPlaying && currentFrame <= totalFrames) {
    const { filename, start, end } = findFileForFrame(currentFrame);

    if (start !== currentFileRange.start) {
      try {
        await loadCompressedFile(filename);
        currentFileRange = { start, end };
      } catch (e) {
        console.error("파일 로딩 실패:", e);
        isPlaying = false;
        return;
      }
    }

    const frameIndex = currentFrame - currentFileRange.start;
    const frameData = currentFileFrames[frameIndex];
    if (!frameData) {
      console.error("프레임 인덱스에 해당하는 데이터가 없습니다:", frameIndex);
      isPlaying = false;
      return;
    }

    try {
      parsedObjects = extractCreaturesFromTurn(JSON.parse(frameData));
    } catch (e) {
      console.error("JSON 파싱 실패:", e, frameData);
      isPlaying = false;
      return;
    }

    currentFrame++;
    preloadNextFiles(currentFrame);  // 항상 다음 프레임들 미리 요청
  }

  // 기존 재생 위치 바 (빨간색)
  document.getElementById("progress").style.width = (currentFrame / totalFrames * 100) + "%";

  // 새로 추가된 버퍼링 바 (회색)
  let maxBufferedFrame = currentFrame;
  for (const filename in frameCache) {
    const { start, end } = findFileForFrame(Number(filename.match(/\d+/)[0]));
    if (end > maxBufferedFrame) maxBufferedFrame = end;
  }
  document.getElementById("buffered").style.width = (maxBufferedFrame / totalFrames * 100) + "%";
  render();
  updateInfoBox();
  requestAnimationFrame(update);
}

// === 렌더링 ===
function render() {
  const frameIndex = currentFrame - currentFileRange.start;
  const frameData = currentFileFrames[frameIndex];
  if (!frameData) return;

  let turnData;
  try {
    turnData = JSON.parse(frameData);
  } catch (e) {
    console.error("렌더링 JSON 파싱 실패:", e, frameData);
    return;
  }

  // ✅ 캔버스 클리어
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // === 화면 범위 계산 ===
  const screenLeftTop = screenToWorld(0, 0);
  const screenRightBottom = screenToWorld(canvas.width, canvas.height);

  const minX = screenLeftTop.x;
  const maxX = screenRightBottom.x;
  const minY = screenLeftTop.y;
  const maxY = screenRightBottom.y;

  // === 유기물 배경 렌더링 (보이는 grid만)
  for (const row of turnData.grids) {
    for (const cell of row) {
      const cellX = cell.pos.x * GRID_SIZE;
      const cellY = cell.pos.y * GRID_SIZE;

      if (
        cellX + GRID_SIZE < minX || cellX > maxX ||
        cellY + GRID_SIZE < minY || cellY > maxY
      ) {
        continue; // ✅ 화면 밖이면 스킵
      }

      const { x, y } = worldToScreen(cellX, cellY);
      const energy = cell.organics.reduce((sum, v) => sum + v, 0);
      const alpha = Math.min(energy / ORGANIC_ENERGY_SCALE, 1.0);
      ctx.fillStyle = `rgba(80, 100, 100, ${alpha.toFixed(2)})`;
      ctx.fillRect(x, y, GRID_SIZE * zoom, GRID_SIZE * zoom);
    }
  }

  // === 생물 렌더링 (보이는 생물만)
  for (const obj of parsedObjects) {
    if (
      obj.x < minX || obj.x > maxX ||
      obj.y < minY || obj.y > maxY
    ) {
      continue; // ✅ 화면 밖이면 스킵
    }

    const { x, y } = worldToScreen(obj.x, obj.y);
    ctx.beginPath();
    ctx.arc(x, y, CREATURE_RADIUS * zoom, 0, Math.PI * 2);
    ctx.fillStyle = (selectedObject && selectedObject.id === obj.id)
      ? `rgb(254,255,192)`
      : `rgb(193,175,255)`;
    ctx.fill();
  }
}

async function detectTotalFrames() {
  const res = await fetch(`${LOG_DIR}index.jsonl`);
  const text = await res.text();
  const lines = text.trim().split("\n");
  const lastLine = lines[lines.length - 1];
  const lastFile = JSON.parse(lastLine);
  const end = parseInt(lastFile.slice(11, 19));
  totalFrames = end;
}

// === 타임바 제어 ===
document.getElementById("timebar").addEventListener("mousedown", e => {
  const rect = e.currentTarget.getBoundingClientRect();
  const ratio = (e.clientX - rect.left) / rect.width;
  currentFrame = Math.floor(ratio * totalFrames);
});

// === 일시정지/재생 버튼 ===
document.getElementById("togglePlayPause").addEventListener("click", () => {
  isPlaying = !isPlaying;
  document.getElementById("togglePlayPause").textContent = isPlaying ? "Pause" : "Play";
});

function debug(text) {  
  const el = document.getElementById("debug");  
  if (el) el.innerText = typeof text === 'object' ? JSON.stringify(text, null, 2) : text;  
}  

async function start() {
  await detectTotalFrames();
  update();
}
start();
