export const frameCount = 300;
export const objectCount = 30;
export const frames = [];

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
