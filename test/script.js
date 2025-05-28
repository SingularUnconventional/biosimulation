// === 캔버스 설정 ===
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
canvas.width = window.innerWidth;
canvas.height = window.innerHeight - 40;

// === 상태 변수 ===
let cameraX = 0, cameraY = 0, zoom = 1;
let isPlaying = true;
let isDragging = false;
let isTouching = false;
let lastTouch = [];
let lastDist = null;
let lastMouse = { x: 0, y: 0 };
let currentFrame = 0;
let parsedObjects = [];
let selectedObject = null;
let lines = [];

// === 터치 및 마우스 인터랙션 ===
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
canvas.addEventListener("touchstart", e => {
  if (e.touches.length === 1) {
    isTouching = true;
    lastTouch = [{ x: e.touches[0].clientX, y: e.touches[0].clientY }];
  } else if (e.touches.length === 2) {
    lastTouch = [
      { x: e.touches[0].clientX, y: e.touches[0].clientY },
      { x: e.touches[1].clientX, y: e.touches[1].clientY }
    ];
    lastDist = getDistance(lastTouch[0], lastTouch[1]);
  }
}, { passive: false });
canvas.addEventListener("touchmove", e => {
  e.preventDefault();
  if (e.touches.length === 1 && isTouching) {
    const current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    const dx = (current.x - lastTouch[0].x) / zoom;
    const dy = (current.y - lastTouch[0].y) / zoom;
    cameraX -= dx;
    cameraY -= dy;
    lastTouch[0] = current;
  } else if (e.touches.length === 2) {
    const p1 = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    const p2 = { x: e.touches[1].clientX, y: e.touches[1].clientY };
    const newDist = getDistance(p1, p2);
    if (lastDist !== null) {
      const zoomFactor = newDist / lastDist;
      const oldZoom = zoom;
      zoom *= zoomFactor;
      const mx = (p1.x + p2.x) / 2;
      const my = (p1.y + p2.y) / 2;
      const rect = canvas.getBoundingClientRect();
      const wx = (mx - rect.left) / oldZoom + cameraX;
      const wy = (my - rect.top) / oldZoom + cameraY;
      cameraX = wx - (mx - rect.left) / zoom;
      cameraY = wy - (my - rect.top) / zoom;
      lastDist = newDist;
    }
    lastTouch = [p1, p2];
  }
}, { passive: false });
canvas.addEventListener("touchend", e => {
  if (e.touches.length < 2) lastDist = null;
  if (e.touches.length === 0) isTouching = false;
});

function getDistance(p1, p2) {
  const dx = p1.x - p2.x;
  const dy = p1.y - p2.y;
  return Math.sqrt(dx * dx + dy * dy);
}

// === 좌표 변환 ===
function worldToScreen(x, y) {
  return {
    x: (x - cameraX) * zoom,
    y: (y - cameraY) * zoom
  };
}
function screenToWorld(x, y) {
  return {
    x: x / zoom + cameraX,
    y: y / zoom + cameraY
  };
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

// === 시뮬레이션 프레임 업데이트 ===
function update() {
  if (isPlaying && currentFrame < lines.length) {
    const parsed = JSON.parse(lines[currentFrame]);
    parsedObjects = extractCreaturesFromTurn(parsed);
    currentFrame++;
  }

  document.getElementById("progress").style.width = (currentFrame / lines.length * 100).toFixed(1) + "%";
  render();
  updateInfoBox();
  requestAnimationFrame(update);
}

// === 렌더링 ===
function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (const obj of parsedObjects) {
    const { x, y } = worldToScreen(obj.x, obj.y);
    ctx.beginPath();
    ctx.arc(x, y, 6 * zoom, 0, Math.PI * 2);
    ctx.fillStyle = (selectedObject && selectedObject.id === obj.id) ? "#FFD700" : "#0cf";
    ctx.fill();
  }
}

// === 객체 클릭 선택 ===
canvas.addEventListener("click", e => {
  const rect = canvas.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;
  const world = screenToWorld(mouseX, mouseY);
  let found = null;
  for (const obj of parsedObjects) {
    const dx = obj.x - world.x;
    const dy = obj.y - world.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist < 10) {
      found = obj;
      break;
    }
  }
  selectedObject = (selectedObject && selectedObject.id === found?.id) ? null : found;
  updateInfoBox();
});

// === 사이드바 정보 표시 ===
function updateInfoBox() {
  const sidebar = document.getElementById("sidebar");
  if (selectedObject) {
    sidebar.innerHTML = `
      <h3>Creature #${selectedObject.id}</h3>
      <p><strong>HP:</strong> ${selectedObject.hp.toFixed(2)}</p>
      <p><strong>Energy:</strong> ${selectedObject.energy.toFixed(4)}</p>
      <p><strong>Position:</strong><br>
         X: ${selectedObject.x.toFixed(2)}<br>
         Y: ${selectedObject.y.toFixed(2)}</p>
    `;
  } else {
    sidebar.innerHTML = "<em>No object selected</em>";
  }
}

// === 타임바 제어 ===
document.getElementById("timebar").addEventListener("mousedown", e => {
  const rect = e.currentTarget.getBoundingClientRect();
  const ratio = (e.clientX - rect.left) / rect.width;
  currentFrame = Math.floor(ratio * lines.length);
});

// === 일시정지/재생 버튼 ===
document.getElementById("togglePlayPause").addEventListener("click", () => {
  isPlaying = !isPlaying;
  document.getElementById("togglePlayPause").textContent = isPlaying ? "Pause" : "Play";
});

// === JSONL 로드 ===
async function loadTurnLogs() {
  const response = await fetch("data/turn_logs.jsonl");
  const text = await response.text();
  lines = text.trim().split("\n");
  update();
}

// === 시작 ===
loadTurnLogs();