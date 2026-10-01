export const definition = {
  apiVersion: 1, label: 'Test and move', runsOn: 'portable',
  inputs: { plan: { kind: 'data', type: 'object', default: {} } },
  outputs: { film: { kind: 'data', type: 'object' } }
} as const;

export function execute(context: any) {
  const { world, scenes } = context.inputs.plan;
  const fps = 30, radius = 0.018, wall = 0.018, step = 0.006;
  const frames: any[] = [], events: any[] = [];
  let p = [...world.origin], blocked = false;
  const valid = (q: number[]) => q[0] >= radius && q[0] <= 1.08 && q[1] >= radius && q[1] <= 1 - radius &&
    !(Math.abs(q[0] - 0.5) < wall + radius && Math.abs(q[1] - world.gapY) > world.gap / 2 - radius);
  const emit = (scene: any, status: string, desired = p) => frames.push({
    p: [...p], desired: [...desired], scene: scene.index, status, lens: scene.lens,
    frame: frames.length, time: frames.length / fps
  });
  for (const scene of scenes) {
    const start = frames.length;
    events.push({ frame: start, scene: scene.index, kind: 'call', text: `Call ${scene.action}` });
    if (!valid(p)) {
      blocked = true; emit(scene, 'blocked');
      events.push({ frame: frames.length - 1, scene: scene.index, kind: 'blocked', text: 'The block starts inside the barrier. Move the start or widen the passage.' });
    } else if (scene.action === 'hold') {
      for (let i = 0; i < scene.duration * fps; i++) emit(scene, 'holding');
    } else {
      for (const target of scene.waypoints) {
        for (let n = 0; n < 400; n++) {
          const dx = target[0] - p[0], dy = target[1] - p[1], distance = Math.hypot(dx, dy);
          if (distance < 0.001) break;
          const amount = Math.min(step, distance);
          const next = [p[0] + dx / distance * amount, p[1] + dy / distance * amount];
          if (!valid(next)) {
            blocked = true; emit(scene, 'blocked', next);
            events.push({ frame: frames.length - 1, scene: scene.index, kind: 'blocked', text: 'The next movement intersects the barrier. This action stops; later scenes wait.' });
            break;
          }
          p = next; emit(scene, 'moving', target);
        }
        if (blocked) break;
      }
      if (!blocked) {
        while (frames.length - start < scene.duration * fps) emit(scene, 'arrived');
      }
    }
    if (blocked) {
      for (let i = 0; i < 30; i++) emit(scene, 'blocked');
      break;
    }
    events.push({ frame: frames.length - 1, scene: scene.index, kind: 'complete', text: `${scene.action} complete` });
  }
  context.outputs.film.set({ frames, events, fps, blocked, scenes, world,
    duration: frames.length / fps, completed: events.filter(e => e.kind === 'complete').length });
}
