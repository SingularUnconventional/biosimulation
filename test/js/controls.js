import { screenToWorld } from './utils.js';
import { updateInfoDisplay } from './ui.js';

export function initMouseEvents(
  canvas,
  getParsedObjects,
  setSelectedObject,
  getSelectedObject,
  setCurrentFrame
) {
  canvas.addEventListener("click", e => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const world = screenToWorld(mouseX, mouseY);

    const parsedObjects = getParsedObjects();
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

    const selected = getSelectedObject();

    if (found) {
      if (selected && selected.id === found.id) {
        setSelectedObject(null);
        document.getElementById("objectInfo").style.display = "none";
      } else {
        setSelectedObject(found);
        updateInfoDisplay(found);
      }
    } else {
      setSelectedObject(null);
      document.getElementById("objectInfo").style.display = "none";
    }
  });

  const timebar = document.getElementById("timebar");

  let isDraggingBar = false;

  timebar.addEventListener("mousedown", e => {
    isDraggingBar = true;
    updateFrameFromMouse(e);
  });

  document.addEventListener("mousemove", e => {
    if (isDraggingBar) updateFrameFromMouse(e);
  });

  document.addEventListener("mouseup", () => isDraggingBar = false);

  function updateFrameFromMouse(e) {
    const rect = timebar.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    const frame = Math.floor(ratio * 300);
    setCurrentFrame(frame);
  }
}

export function initPauseControl(togglePause) {
  document.addEventListener("keydown", e => {
    if (e.key === ' ') {
      e.preventDefault();
      togglePause();
    }
  });
}
