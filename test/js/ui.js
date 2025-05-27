import { worldToScreen } from './utils.js';
import { selectedObject } from './main.js';

export function updateInfoBox() {
  if (selectedObject) {
    const { x, y } = worldToScreen(selectedObject.x, selectedObject.y);
    const infoBox = document.getElementById("objectInfo");
    infoBox.style.left = (x + 10) + "px";
    infoBox.style.top = (y - 10) + "px";
  }
}

export function updateInfoDisplay(obj) {
  const infoBox = document.getElementById("objectInfo");
  infoBox.innerHTML = `<b>Object #${obj.id}</b><br>HP: ${obj.hp}`;
  infoBox.style.display = "block";
}
