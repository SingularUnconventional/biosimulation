import { zoom, camera } from './utils.js';

export function initCameraEvents(canvas) {
  let isDragging = false;
  let lastMouse = { x: 0, y: 0 };

  canvas.addEventListener("mousedown", e => {
    isDragging = true;
    lastMouse = { x: e.clientX, y: e.clientY };
  });

  canvas.addEventListener("mouseup", () => isDragging = false);

  canvas.addEventListener("mousemove", e => {
    if (isDragging) {
      const dx = (e.clientX - lastMouse.x) / zoom.value;
      const dy = (e.clientY - lastMouse.y) / zoom.value;
      camera.x -= dx;
      camera.y -= dy;
      lastMouse = { x: e.clientX, y: e.clientY };
    }
  });

  canvas.addEventListener("wheel", e => {
    const zoomFactor = 1.1;
    const oldZoom = zoom.value;
    zoom.value = e.deltaY < 0 ? zoom.value * zoomFactor : zoom.value / zoomFactor;

    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const wx = mx / oldZoom + camera.x;
    const wy = my / oldZoom + camera.y;
    camera.x = wx - mx / zoom.value;
    camera.y = wy - my / zoom.value;

    e.preventDefault();
  });
}
