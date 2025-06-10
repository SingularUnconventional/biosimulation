// === 캔버스 및 기본 설정 ===
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
canvas.width = window.innerWidth;
canvas.height = window.innerHeight - 40;

const CONFIG = {
  GRID_SIZE: 40,
  ORGANIC_ENERGY_SCALE: 10000000000.0,
  CREATURE_RADIUS: 1,
  FRAMES_PER_FILE: 100,
  LOG_DIR: "/logs/compressed/",
  CREATURE_SHEET_DIR: "/logs/creature_sheet.png",
  CREATURE_SIZE_DIR: "/logs/creature_sheet_size.jsonl",
  TERRAIN_ALTITUDE_DIR: "/logs/terrain",
  MAX_CACHE_FILES: 4,
  PRELOAD_LOOKAHEAD: 3,
  GENE_FETCH_ZOOM_THRESHOLD: 2,
  GENE_CACHE_LIMIT: 10000,
};

const state = {
  cameraX: 0, cameraY: 0, zoom: 1,
  isPlaying: true, isDragging: false, isTouching: false,
  lastMouse: { x: 0, y: 0 }, lastTouch: [], lastDist: null,
  tapStartPos: null, tapStartTime: 0,
  currentFrame: 1, totalFrames: 0,
  selectedObject: null, selectedObjectData: null,
  currentFileFrames: [], currentFileRange: { start: -1, end: -1 },

  visibleGridRange: { minX: 0, maxX: 0, minY: 0, maxY: 0 },
  visibleGrids: [],
  visibleCreatures: [],
  visibleCorpses: [],
};

const cache = {
  queue: new Map(),
  frameCache: {},
  loadPromises: {},

  geneCache: new Map(),     // id → gene
  geneRequestQueue: new Set(),
  geneQueueList: [],
};

const CreatureSheetCache = {
  sheetImage: null,  // HTMLImageElement
  sizeArray: [],
  ready: false,
};

//  지형 고도별 색상 사전 정의
const terrainColors = Array.from({ length: 21 }, (_, h) => {
  if (h <= 7) return '#322be1';      // deepblue
  if (h === 8) return '#3956e6';
  if (h <= 9) return '#4169e1';      // blue
  if (h === 10) return '#00bfff';     // lightblue
  if (h <= 11) return '#eed6af';      // beach
  if (h <= 12) return '#228b22';     // green
  if (h <= 14) return '#006400';     // darkgreen
  if (h <= 16) return '#8b8989';     // mountain
  return '#fffafa';                  // snow
});
// 고도 데이터 전역 변수
let terrainAltitude = [];

// === 유틸 함수 ===
const worldToScreen = (x, y) => ({ x: (x - state.cameraX) * state.zoom, y: (y - state.cameraY) * state.zoom });
const screenToWorld = (x, y) => ({ x: x / state.zoom + state.cameraX, y: y / state.zoom + state.cameraY });

function findFileForFrame(frame) {
  const end = Math.ceil(frame / CONFIG.FRAMES_PER_FILE) * CONFIG.FRAMES_PER_FILE;
  return { filename: `turn_logs_${String(end).padStart(8, "0")}.zst`, start: end - CONFIG.FRAMES_PER_FILE + 1, end };
}

async function fetchAndParseFile(filename) {
  const res = await fetch(`${CONFIG.LOG_DIR}${filename}`);
  const buf = await res.arrayBuffer();
  return new TextDecoder("utf-8").decode(buf).trim().split("\n");
}

async function loadCompressedFile(filename) {
  if (cache.frameCache[filename]) return cache.frameCache[filename];
  if (!cache.loadPromises[filename]) {
    cache.loadPromises[filename] = fetchAndParseFile(filename).then(frames => {
      cacheFile(filename, frames);
      return frames;
    }).catch(e => { delete cache.loadPromises[filename]; throw e; });
  }
  return cache.loadPromises[filename];
}

function preloadNextFiles(currentFrame) {
  for (let i = 1; i <= CONFIG.PRELOAD_LOOKAHEAD; i++) {
    const { filename } = findFileForFrame(currentFrame + i * CONFIG.FRAMES_PER_FILE);
    if (!cache.loadPromises[filename]) {
      cache.loadPromises[filename] = fetchAndParseFile(filename).then(frames => {
        cacheFile(filename, frames);
        return frames;
      }).catch(() => delete cache.loadPromises[filename]);
    }
  }
}

function cacheFile(filename, frames) {
  cache.frameCache[filename] = frames;
  if (cache.queue.has(filename)) cache.queue.delete(filename);
  cache.queue.set(filename, true);
  while (cache.queue.size > CONFIG.MAX_CACHE_FILES) {
    const oldest = cache.queue.keys().next().value;
    cache.queue.delete(oldest);
    delete cache.frameCache[oldest];
    delete cache.loadPromises[oldest];
  }
}

async function fetchGeneInfo(id) {
  if (cache.geneCache.has(id)) return cache.geneCache.get(id);
  if (cache.geneRequestQueue.has(id)) return cache.geneCache.get(id);
  cache.geneRequestQueue.add(id);

  try {
    const res = await fetch(`/logs/${id}`);
    if (!res.ok) throw new Error("유전자 요청 실패");
    const geneInfo = await res.json();
    cache.geneCache.set(id, geneInfo);
    cache.geneQueueList.push(id);

    if (cache.geneQueueList.length > CONFIG.GENE_CACHE_LIMIT) {
      const oldest = cache.geneQueueList.shift();
      cache.geneCache.delete(oldest);
    }
  } catch (e) {
    console.warn(`❌ 유전자 정보 로드 실패 (id: ${id})`, e);
  } finally {
    cache.geneRequestQueue.delete(id);
    return cache.geneCache.get(id);
  }
}

// === 유틸: 현재 가시 그리드 범위 계산
function updateVisibleGridRange() {
  const { x: minX, y: minY } = screenToWorld(0, 0);
  const { x: maxX, y: maxY } = screenToWorld(canvas.width, canvas.height);
  state.visibleGridRange = {
    minX: Math.floor(minX / CONFIG.GRID_SIZE),
    maxX: Math.ceil(maxX / CONFIG.GRID_SIZE),
    minY: Math.floor(minY / CONFIG.GRID_SIZE),
    maxY: Math.ceil(maxY / CONFIG.GRID_SIZE),
  };
}

// === 유틸: 현재 프레임에서 가시 범위 데이터 추출
function extractVisibleFromTurn(turnData) {
  const grids = turnData[1];
  const creatures = [];
  const corpses = [];
  const visibleGrids = [];
  const { minX, maxX, minY, maxY } = state.visibleGridRange;

  for (let y = minY; y <= maxY; y++) {
    if (!grids[y]) continue;
    for (let x = minX; x <= maxX; x++) {
      const cell = grids[y][x];
      if (!cell) continue;
      const [organics, creatureList, corpsesList] = cell;
      visibleGrids.push({ x, y, organics });

      for (const [id, cx, cy, hp, energy, brain_nodes] of creatureList) {
        creatures.push({
          id,
          x: cx,
          y: cy,
          hp,
          energy,
          brain_nodes,
        });
      }

      for (const [cx, cy, energy] of corpsesList) {
        corpses.push({ x: cx, y: cy, energy });
      }
    }
  }

  state.visibleGrids = visibleGrids;
  state.visibleCreatures = creatures;
  state.visibleCorpses = corpses;
}


const CreatureImageCache = new Map();

function extractCreatureByIndex(index, tileSize = 16) {
  if (CreatureImageCache.has(index)) return CreatureImageCache.get(index);

  const sheet = CreatureSheetCache.sheetImage;
  const cx = index * tileSize;

  const canvas = document.createElement("canvas");
  canvas.width = tileSize;
  canvas.height = tileSize * 2;

  const ctx = canvas.getContext("2d");
  ctx.drawImage(sheet, cx, 0, tileSize, tileSize * 2, 0, 0, tileSize, tileSize * 2);

  CreatureImageCache.set(index, canvas); // 캐시 저장
  return canvas;
}

function handleObjectSelection(screenX, screenY) {
  const world = screenToWorld(screenX, screenY);
  state.selectedObject = state.visibleCreatures.find(obj => Math.hypot(obj.x - world.x, obj.y - world.y) < CreatureSheetCache.sizeArray[obj.id]/2);
  fetchGeneInfo(state.selectedObject.id).then(data => {
    state.selectedObjectData = data;
  });
  // updateInfoBox();
  // console.debug(`${found}`)
  // console.debug(`${state.selectedObject}`)
}
function updateInfoBox() {
  const sidebar = document.getElementById("sidebar");
  const latest = state.visibleCreatures.find(obj => obj.id === state.selectedObject?.id);
  if (!latest) {
    sidebar.innerHTML = `<div class="info-empty">No object selected</div>`;
    return;
  }

  const lines = [
    `<div class="info-header">Creature #${latest.id}</div>`,
    `<div class="info-row"><span class="label">HP</span><span class="value">${latest.hp.toFixed(2)}</span></div>`,
    `<div class="info-row"><span class="label">Energy</span><span class="value">${latest.energy.toFixed(4)}</span></div>`,
    `<div class="info-row"><span class="label">Position</span><span class="value">X: ${latest.x.toFixed(2)}<br>Y: ${latest.y.toFixed(2)}</span></div>`,
    `<div class="info-row"><span class="label">Brain nodes</span><span class="value">${latest.brain_nodes.join(", ")}</span></div>`,
  ];

  if (state.selectedObjectData) {
    lines.push(`<div class="info-section">
      <div class="info-subtitle">Genome</div>
      <pre class="gene-box">${JSON.stringify(state.selectedObjectData, null, 2)}</pre>
    </div>`);
  }

  sidebar.innerHTML = lines.join("\n");
}

// === 렌더링 ===
function render() {
  const frameIndex = state.currentFrame - state.currentFileRange.start;
  const frameData = state.currentFileFrames[frameIndex];
  if (!frameData) return;

  let turnData;
  try {
    turnData = JSON.parse(frameData);
  } catch (e) {
    console.error("렌더링 JSON 파싱 실패:", e);
    return;
  }

  const grids = turnData[1];
  if (!Array.isArray(grids)) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.imageSmoothingEnabled = false;

  for (const { x, y, organics } of state.visibleGrids) {
    const gx = x * CONFIG.GRID_SIZE;
    const gy = y * CONFIG.GRID_SIZE;
    const { x: sx, y: sy } = worldToScreen(gx, gy);

    // 고도 기반 색상
    const baseColor = terrainAltitude?.[y]?.[x] ?? 0;

    // // 유기물 기반 알파값 계산
    // const energy = organics.reduce((a, b) => a + b, 0);
    // const alpha = Math.min(energy / CONFIG.ORGANIC_ENERGY_SCALE, 1.0).toFixed(2);

    ctx.fillStyle = baseColor;
    ctx.fillRect(sx, sy, CONFIG.GRID_SIZE * state.zoom, CONFIG.GRID_SIZE * state.zoom);

    // ctx.fillStyle = `rgba(0,0,0,${alpha})`;  // 유기물 오버레이
    // ctx.fillRect(sx, sy, CONFIG.GRID_SIZE * state.zoom, CONFIG.GRID_SIZE * state.zoom);
  }

  for (const obj of state.visibleCorpses) {
    const { x, y } = worldToScreen(obj.x, obj.y);
    ctx.beginPath();
    ctx.arc(x, y, CONFIG.CREATURE_RADIUS * state.zoom/2, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(204,255,102,${Math.min(obj.energy / 5000, 1.0).toFixed(2)})`;
    ctx.fill();
  }

  const shouldFetchImg = state.zoom >= CONFIG.GENE_FETCH_ZOOM_THRESHOLD
  for (const obj of state.visibleCreatures) {
    const { x, y } = worldToScreen(obj.x, obj.y);

    const isSelected = state.selectedObject?.id === obj.id;
    const drawSize = CreatureSheetCache.sizeArray[obj.id] * state.zoom;

    if(shouldFetchImg){
      let creatureCanvas = null;

      if (obj.id !== undefined && CreatureSheetCache.ready) {
        // 미리 추출된 이미지를 obj에 할당해 두었거나, 실시간 추출
        creatureCanvas = obj.imageCanvas ?? extractCreatureByIndex(obj.id);
        obj.imageCanvas = creatureCanvas; // 캐시 (선택)
      }

      if (creatureCanvas) {
        ctx.drawImage(
          creatureCanvas,
          x - drawSize / 2,
          y - drawSize,
          drawSize,
          drawSize * 2
        );
      }
      
    } else {
      ctx.beginPath();
        ctx.arc(x, y, drawSize*CONFIG.CREATURE_RADIUS/2, 0, Math.PI * 2);
        ctx.fillStyle = "rgb(100,100,100)";
        ctx.fill();
    }
  }
}

// === 프레임 업데이트 ===
async function update() {
  if (state.currentFrame <= state.totalFrames) {
    const { filename, start, end } = findFileForFrame(state.currentFrame);
    const frameIndex = state.currentFrame - start;

    const needsLoad = !cache.frameCache[filename] || state.currentFileRange.start !== start;
    if (needsLoad) {
      try {
        const frames = await loadCompressedFile(filename);
        state.currentFileFrames = frames;
        state.currentFileRange = { start, end };
      } catch (e) {
        console.error("❌ 파일 로딩 실패:", e);
        state.isPlaying = false;
        return;
      }
    }

    const frameData = state.currentFileFrames[frameIndex];
    if (!frameData) {
      console.warn("⚠️ 존재하지 않는 프레임:", frameIndex);
      state.isPlaying = false;
      return;
    }

    try {
      const turnData = JSON.parse(frameData);
      extractVisibleFromTurn(turnData);
    } catch (e) {
      console.error("❌ JSON 파싱 실패:", e);
      state.isPlaying = false;
      return;
    }
    if(state.isPlaying){
      state.currentFrame++;
    }
  }
  
  preloadNextFiles(state.currentFrame);
  render();
  updateInfoBox();

  document.getElementById("progress").style.width = (state.currentFrame / state.totalFrames * 100) + "%";
  let maxBuffered = state.currentFrame;
  for (const filename in cache.frameCache) {
    const { end } = findFileForFrame(Number(filename.match(/\d+/)[0]));
    if (end > maxBuffered) maxBuffered = end;
  }
  document.getElementById("buffered").style.width = (maxBuffered / state.totalFrames * 100) + "%";

  requestAnimationFrame(update);
}

// === 초기화 ===
document.getElementById("togglePlayPause").addEventListener("click", () => {
  state.isPlaying = !state.isPlaying;
  document.getElementById("togglePlayPause").textContent = state.isPlaying ? "Pause" : "Play";
});

document.getElementById("timebar").addEventListener("mousedown", e => {
  const rect = e.currentTarget.getBoundingClientRect();
  state.currentFrame = Math.floor(((e.clientX - rect.left) / rect.width) * state.totalFrames);
});

canvas.addEventListener("mousedown", e => {
  state.isDragging = true;
  state.lastMouse = { x: e.clientX, y: e.clientY };
});
canvas.addEventListener("mouseup", () => state.isDragging = false);
canvas.addEventListener("mousemove", e => {
  if (!state.isDragging) return;
  const dx = (e.clientX - state.lastMouse.x) / state.zoom;
  const dy = (e.clientY - state.lastMouse.y) / state.zoom;
  state.cameraX -= dx;
  state.cameraY -= dy;
  state.lastMouse = { x: e.clientX, y: e.clientY };
  updateVisibleGridRange();
});
canvas.addEventListener("wheel", e => {
  const factor = e.deltaY < 0 ? 1.1 : 1 / 1.1;
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  const wx = mx / state.zoom + state.cameraX, wy = my / state.zoom + state.cameraY;
  state.zoom *= factor;
  state.cameraX = wx - mx / state.zoom;
  state.cameraY = wy - my / state.zoom;
  e.preventDefault();
  updateVisibleGridRange();
});
canvas.addEventListener("click", e => {
  const rect = canvas.getBoundingClientRect();
  handleObjectSelection(e.clientX - rect.left, e.clientY - rect.top);
});

canvas.addEventListener("touchstart", e => {
  if (e.touches.length === 1) {
    state.isTouching = true;
    state.lastTouch = [{ x: e.touches[0].clientX, y: e.touches[0].clientY }];
    state.tapStartTime = Date.now();
    state.tapStartPos = state.lastTouch[0];
    state.lastDist = null;
  } else if (e.touches.length === 2) {
    state.lastTouch = [...e.touches].map(t => ({ x: t.clientX, y: t.clientY }));
    state.lastDist = Math.hypot(
      state.lastTouch[0].x - state.lastTouch[1].x,
      state.lastTouch[0].y - state.lastTouch[1].y
    );
  }
  e.preventDefault();
}, { passive: false });

canvas.addEventListener("touchmove", e => {
  if (e.touches.length === 1 && state.isTouching) {
    const dx = (e.touches[0].clientX - state.lastTouch[0].x) / state.zoom;
    const dy = (e.touches[0].clientY - state.lastTouch[0].y) / state.zoom;
    state.cameraX -= dx;
    state.cameraY -= dy;
    state.lastTouch = [{ x: e.touches[0].clientX, y: e.touches[0].clientY }];
    updateVisibleGridRange();
  } else if (e.touches.length === 2) {
    const touch = [...e.touches].map(t => ({ x: t.clientX, y: t.clientY }));
    const dist = Math.hypot(touch[0].x - touch[1].x, touch[0].y - touch[1].y);
    if (state.lastDist) {
      const scale = dist / state.lastDist;
      const midX = (touch[0].x + touch[1].x) / 2;
      const midY = (touch[0].y + touch[1].y) / 2;
      const wx = midX / state.zoom + state.cameraX, wy = midY / state.zoom + state.cameraY;
      state.zoom *= scale;
      state.cameraX = wx - midX / state.zoom;
      state.cameraY = wy - midY / state.zoom;
      updateVisibleGridRange();
    }
    state.lastTouch = touch;
    state.lastDist = dist;
  }
  e.preventDefault();
}, { passive: false });

canvas.addEventListener("touchend", e => {
  state.isTouching = false;
  state.lastTouch = [];
  state.lastDist = null;
  if (e.changedTouches.length === 1 && state.tapStartPos) {
    const touch = e.changedTouches[0];
    if (Math.hypot(touch.clientX - state.tapStartPos.x, touch.clientY - state.tapStartPos.y) < 10 &&
        Date.now() - state.tapStartTime < 300) {
      const rect = canvas.getBoundingClientRect();
      handleObjectSelection(touch.clientX - rect.left, touch.clientY - rect.top);
    }
  }
});

async function loadTerrainAltitude() {
  const res = await fetch(CONFIG.TERRAIN_ALTITUDE_DIR);
  const json = await res.json();
  const raw = json.altitude;

  terrainAltitude = raw.map(row => row.map(h => terrainColors[h]));
}

async function preloadCreatureSheetAndSize(sheetUrl=CONFIG.CREATURE_SHEET_DIR, sizeUrl=CONFIG.CREATURE_SIZE_DIR) {
  // 1. 이미지 로드
  const img = new Image();
  const imageLoaded = new Promise((resolve, reject) => {
    img.onload = resolve;
    img.onerror = reject;
  });
  img.src = sheetUrl;
  await imageLoaded;

  CreatureSheetCache.sheetImage = img;

  // 2. size.jsonl 로드
  const response = await fetch(sizeUrl);
  const text = await response.text();
  CreatureSheetCache.sizeArray = text
    .trim()
    .split("\n")
    .map(Number); // ← 실수 배열로 변환

  CreatureSheetCache.ready = true;
}

async function detectTotalFrames() {
  const text = await (await fetch(`${CONFIG.LOG_DIR}index.jsonl`)).text();
  const lastLine = text.trim().split("\n").pop();
  state.totalFrames = parseInt(JSON.parse(lastLine).slice(11, 19));
}

(async function start() {
  await loadTerrainAltitude();
  await preloadCreatureSheetAndSize();
  await detectTotalFrames();
  const { filename, start, end } = findFileForFrame(state.currentFrame);
  state.currentFileFrames = await loadCompressedFile(filename);
  state.currentFileRange = { start, end };
  update();
})();
