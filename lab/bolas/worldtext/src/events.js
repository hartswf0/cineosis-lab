// node events.js -> JSON: for each scene, the local times at which Bolas attaches a thread (from stage.js itself)
const path = require('path');
const deck = require(path.join(__dirname, '..', 'deck.js'));
global.window = undefined;
require(path.join(__dirname, '..', 'timing.js'));
const STAGE = require(path.join(__dirname, '..', 'stage.js'));
const tm = STAGE.timingFor(deck, globalThis.TIMING);
console.log(JSON.stringify(deck.scenes.map((s, i) => STAGE.events(deck, tm, i).filter(x => x >= 0 && x < tm.scenes[i].d).sort((a, b) => a - b))));
