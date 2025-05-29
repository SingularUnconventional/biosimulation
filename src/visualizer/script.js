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

let currentFrame = 1;
let totalFrames = 0;
let parsedObjects = [];
let selectedObject = null;
let currentFileFrames = [];
let currentFileRange = { start: -1, end: -1 };
let preloadCache = {};  // filename => frames[]
let preloadingFile = null;

function worldToScreen(x, y) {
  return { x: (x - cameraX) * zoom, y: (y - cameraY) * zoom };
}
function screenToWorld(x, y) {
  return { x: x / zoom + cameraX, y: y / zoom + cameraY };
}

// === 마우스 및 터치 인터랙션 ===
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
  const world = screenToWorld(mouseX, mouseY);
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
});

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

async function loadCompressedFile(filename) {
  if (preloadCache[filename]) {
    currentFileFrames = preloadCache[filename];
    delete preloadCache[filename];
    return;
  }

  const res = await fetch(`${LOG_DIR}${filename}`);
  const text = await res.text();

  if (!text.trim()) throw new Error(`압축 해제된 로그가 비어있습니다: ${filename}`);
  currentFileFrames = text.trim().split("\n");
  if (currentFileFrames.length === 0) throw new Error(`프레임 파싱 실패: ${filename}`);
}

async function preloadNextFile(filename) {
  preloadingFile = filename;
  try {
    const res = await fetch(`${LOG_DIR}${filename}`);
    const text = await res.text();
    const frames = text.trim().split("\n");
    if (frames.length > 0) preloadCache[filename] = frames;
  } catch (e) {
    console.warn(`❗️프리로드 실패: ${filename}`, e);
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

    let parsed;
    try {
      parsed = JSON.parse(frameData);
    } catch (e) {
      console.error("JSON 파싱 실패:", e, frameData);
      isPlaying = false;
      return;
    }

    parsedObjects = extractCreaturesFromTurn(parsed);
    currentFrame++;

    const nextRange = findFileForFrame(currentFileRange.end + 1);
    if (!preloadingFile || preloadingFile !== nextRange.filename) {
      preloadNextFile(nextRange.filename);
    }
  }

  document.getElementById("progress").style.width = (currentFrame / totalFrames * 100) + "%";
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

async function start() {
  await detectTotalFrames();
  update();
}
start();
