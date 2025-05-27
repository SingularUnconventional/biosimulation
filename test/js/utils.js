export const camera = { x: 0, y: 0 };
export const zoom = { value: 1 };

export function worldToScreen(x, y) {
  return {
    x: (x - camera.x) * zoom.value,
    y: (y - camera.y) * zoom.value
  };
}

export function screenToWorld(x, y) {
  return {
    x: x / zoom.value + camera.x,
    y: y / zoom.value + camera.y
  };
}
