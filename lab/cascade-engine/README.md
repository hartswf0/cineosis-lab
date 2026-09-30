# Cascade Engine

An independent Cineosis Lab study: words call actions, actions propose routes, and a bounded motor tests those routes against a visible world. The resulting state sequence is assembled into procedural shots. Existing Shannon, Markov, and archive tools are unchanged.

Open `../cascade-engine.html` over HTTP. The committed browser bundle has no server API dependency. It uses the actual `@field/cascade` 0.7.1 neutral runtime, not an imitation of its graph executor.

## Build

Node 24 or newer (tests use native TypeScript stripping):

```
npm ci
npm run check
npm test
npm run build
npx cascade run index.cascade
```

`index.cascade` is a portable three-node graph. `engine.js` registers the same node definitions and connections with Cascade. `Score` validates explicit scene actions, `Route` expands intermediate destinations, and `Motor` emits complete deterministic frames and causal events. The browser renders and scrubs those outputs. There is no random source or ambient clock inside a node. Playback time never changes the computed trajectory.

## Interaction contract

- **Surface hidden state:** show predicted completion, the active action, a collision stop, suspended scenes, routes, and actual node inputs and consequences in Trace.
- **Reduce memory burden:** keep the score beside the world, number scenes and stones, retain complete takes, and show the previous route during comparison.
- **Multiple modes:** World, Film, and Trace use the same computed frames and selected time.
- **Direct manipulation:** dragging the passage, start, destination, or stones recomposes the sequence. Sliders and numeric controls provide keyboard alternatives.
- **Semantic zoom:** select a causal stage, then select it again for frame/position detail. Film changes framing by action; the active scene stays selected in the score.
- **Constrained play:** every spatial step is checked, unsuccessful actions stop, edits can be undone, saved takes restore complete state, and sessions can be exported/imported.

## Deliberate limits

This version creates silent abstract films of a single block in a two-dimensional world. It does not retrieve archive footage, invoke Shannon, transcribe speech, infer arbitrary literary meaning, or learn motor policies. Text import is an explicit small verb lexicon; unmatched lines become holds and all actions remain editable. The example studies are original scores inspired by structural ideas, not poem quotations or literary comprehension tests.

Up to eight scenes, five stepping stones, twelve kept takes, and forty undo states. Coordinates are normalized; the motor uses a conservative square collision envelope, a 3.6% body width, and 0.6% movement steps. A blocked action suspends subsequent scenes. Scene duration is a minimum: movement can take longer. Return reverses the authored stones. A stepping stone is a proposed point, not permission to pass through an obstruction.

Sessions are stored in localStorage and contain no media or credentials. Exported JSON includes the score, world, saved takes, and graph definition. Imported sessions are size- and shape-checked before replacing state. Video export uses the browser's supported MediaRecorder format and captures in real time; it is silent and should remain in a foreground tab.

## Next engine boundary

The film output is `{ frames, events, scenes, world, fps, duration, blocked, completed }`. Each frame includes position, intended position, scene, status, and lens. A future archive adapter can consume these temporal and causal requirements, propose shots, and report unmet requirements without changing the motor. That adapter is not part of this build.

## Dependency license

FIELD.IO Cascade is MIT licensed. Its license is included in `CASCADE-LICENSE.txt`. Rebuild the committed `dist/app.js` after editing source.
