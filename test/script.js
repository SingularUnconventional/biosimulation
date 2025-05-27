const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const infoBox = document.getElementById("objectInfo");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight - 40;

let cameraX = 0, cameraY = 0, zoom = 1;
let isPlaying = true;
let isDragging = false;
let isTouching = false;
let lastTouch = [];
let lastDist = null;

let lastMouse = { x: 0, y: 0 };

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
});

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

      // 중심점 기준 줌
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

// ==== 데이터 생성 ====
const frames = [];
const objectCount = 30;
const frameCount = 300;

for (let t = 0; t < frameCount; t++) {
  const objects = [];
  for (let i = 0; i < objectCount; i++) {
    const angle = (t + i * 20) * 0.02;
    objects.push({
      id: i,
      x: Math.cos(angle) * 200 + i * 10,
      y: Math.sin(angle) * 200 + i * 10,
      hp: 100 - ((t + i) % 100)
    });
  }
  frames.push(JSON.stringify({ time: t, objects }));
}

let currentFrame = 0;
let parsedObjects = [];
let selectedObject = null;

function update() {
  if (isPlaying && currentFrame < frames.length) {
    const line = frames[currentFrame];
    const parsed = JSON.parse(line);
    parsedObjects = parsed.objects;
    currentFrame++;
  }

  document.getElementById("progress").style.width = (currentFrame / frameCount * 100).toFixed(1) + "%";

  render();
  updateInfoBox();
  requestAnimationFrame(update);
}

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

  if (found) {
    selectedObject = (selectedObject && selectedObject.id === found.id) ? null : found;
  } else {
    selectedObject = null;
  }

  updateInfoBox();
});

function updateInfoBox() {
  if (selectedObject) {
    const sidebar = document.getElementById("sidebar");
    sidebar.innerHTML = `
      <h3>Object #${selectedObject.id}</h3>
      <p><strong>HP:</strong> ${selectedObject.hp}</p>
      <p><strong>Position:</strong><br>X: ${selectedObject.x.toFixed(2)}<br>Y: ${selectedObject.y.toFixed(2)}</p>
    `;
  } else {
    document.getElementById("sidebar").innerHTML = "<em>No object selected</em>";
  }
}
document.getElementById("timebar").addEventListener("mousedown", e => {
  const rect = e.currentTarget.getBoundingClientRect();
  const ratio = (e.clientX - rect.left) / rect.width;
  currentFrame = Math.floor(ratio * frameCount);
});

document.getElementById("togglePlayPause").addEventListener("click", () => {
  isPlaying = !isPlaying;
  document.getElementById("togglePlayPause").textContent = isPlaying ? "Pause" : "Play";
});
update();
