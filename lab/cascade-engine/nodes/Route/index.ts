export const definition = {
  apiVersion: 1, label: 'Propose a route', runsOn: 'portable',
  inputs: {
    cues: { kind: 'data', type: 'object', default: { cues: [] } },
    world: { kind: 'data', type: 'object', default: {} }
  },
  outputs: { plan: { kind: 'data', type: 'object' } }
} as const;

export function execute(context: any) {
  const world = context.inputs.world;
  const route = world.stones.map((p: number[]) => [...p]);
  const scenes = context.inputs.cues.cues.map((cue: any) => ({
    ...cue,
    waypoints: cue.action === 'cross' ? [...route, world.target] :
      cue.action === 'return' ? [...route].reverse().concat([world.origin]) :
      cue.action === 'depart' ? [[1.06, world.target[1]]] : [],
    lens: cue.action === 'hold' ? 'close' : (cue.action === 'return' || cue.action === 'depart') ? 'wide' : 'follow'
  }));
  context.outputs.plan.set({ world, scenes });
}
