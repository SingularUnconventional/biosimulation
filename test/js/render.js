import { ctx, parsedObjects, selectedObject } from './main.js';
import { worldToScreen } from './utils.js';
import { zoom } from './utils.js';

export function renderFrame() {
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  for (const obj of parsedObjects) {
    const { x, y } = worldToScreen(obj.x, obj.y);
    ctx.beginPath();
    ctx.arc(x, y, 6 * zoom.value, 0, Math.PI * 2);
    ctx.fillStyle = (selectedObject && selectedObject.id === obj.id) ? "#FFD700" : "#0cf";
    ctx.fill();
  }
}
