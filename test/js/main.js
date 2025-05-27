// js/main.js
import { initCameraEvents } from './camera.js';
import { initMouseEvents, initPauseControl } from './controls.js';
import { renderFrame } from './render.js';
import { updateInfoBox } from './ui.js';
import { frames, frameCount } from './data.js';

// === 주요 상태 ===
export let currentFrame = 0;
export let parsedObjects = [];
export let selectedObject = null;

// === canvas 설정 ===
const canvas = document.getElementById("canvas");
export const ctx = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight - 40;

let isPaused = false;

function update() {
  if (!isPaused && currentFrame < frameCount) {
    const parsed = JSON.parse(frames[currentFrame]);
    parsedObjects = parsed.objects;
    currentFrame++;
  }

  document.getElementById("progress").style.width =
    (currentFrame / frameCount * 100).toFixed(1) + "%";

  renderFrame();
  updateInfoBox();
  requestAnimationFrame(update);
}

initCameraEvents(canvas);
initMouseEvents(
  canvas,
  () => parsedObjects,
  obj => selectedObject = obj,
  () => selectedObject,
  f => currentFrame = f
);
initPauseControl(() => isPaused = !isPaused);
update();