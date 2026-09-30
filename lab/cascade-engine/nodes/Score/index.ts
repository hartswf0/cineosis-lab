export const definition = {
  apiVersion: 1, label: 'Read the score', runsOn: 'portable',
  inputs: { score: { kind: 'data', type: 'object', default: { cues: [] } } },
  outputs: { cues: { kind: 'data', type: 'object' } }
} as const;

export function execute(context: any) {
  const actions = ['cross', 'hold', 'return', 'depart'];
  const cues = context.inputs.score.cues.slice(0, 8).map((cue: any, i: number) => ({
    text: String(cue.text).slice(0, 240),
    action: actions.includes(cue.action) ? cue.action : 'hold',
    duration: Math.max(0.5, Math.min(8, Number(cue.duration) || 2)), index: i
  }));
  context.outputs.cues.set({ cues });
}
