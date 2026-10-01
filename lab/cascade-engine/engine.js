import { createRuntime } from '@field/cascade/runtime';
import * as Score from './nodes/Score/index.ts';
import * as Route from './nodes/Route/index.ts';
import * as Motor from './nodes/Motor/index.ts';

export const graphDocument = {
  version: '1.0',
  nodes: [
    { id: 'score', module: 'project.Score' },
    { id: 'route', module: 'project.Route' },
    { id: 'motor', module: 'project.Motor' }
  ],
  connections: [
    { source: { nodeId: 'score', outputName: 'cues' }, target: { nodeId: 'route', inputName: 'cues' } },
    { source: { nodeId: 'route', outputName: 'plan' }, target: { nodeId: 'motor', inputName: 'plan' } }
  ]
};

export async function createEngine() {
  const runtime = createRuntime({
    host: { environment: typeof window === 'undefined' ? 'server' : 'browser', capabilities: {},
      modules: { resolve: async () => null }, now: () => 0, report: () => {} },
    nodes: [Score, Route, Motor].map((module, i) => ({ kind: 'definition-v1',
      moduleId: ['project.Score', 'project.Route', 'project.Motor'][i],
      definition: module.definition, loadExecute: async () => module.execute }))
  });
  const graph = await runtime.load(graphDocument);
  return {
    async compose(score, world) {
      await graph.setInput('score', 'score', { cues: score });
      await graph.setInput('route', 'world', world);
      const result = await graph.run();
      if (result.status !== 'completed') throw new Error(result.diagnostics.map(d => d.message).join('; '));
      return graph.getOutput('motor', 'film');
    },
    inspect: () => graph.inspect(), dispose: () => runtime.dispose()
  };
}

export const initial = () => ({
  title: 'Where you go when you leave',
  cues: [
    { text: 'I go towards the other side.', action: 'cross', duration: 2 },
    { text: 'I stay there for a moment.', action: 'hold', duration: 2 },
    { text: 'I return to where I began.', action: 'return', duration: 2 }
  ],
  world: { origin: [0.16, 0.67], target: [0.84, 0.67], gapY: 0.29, gap: 0.22, stones: [] }
});

export function suggest(text) {
  if (/\b(return|back|again|home)\b/i.test(text)) return 'return';
  if (/\b(leave|leaves|depart|gone|away)\b/i.test(text)) return 'depart';
  if (/\b(go|goes|cross|walk|walks|through|towards|toward|reach|journey)\b/i.test(text)) return 'cross';
  return 'hold';
}
