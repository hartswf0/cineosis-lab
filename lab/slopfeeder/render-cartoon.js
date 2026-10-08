// node slopfeeder/render-cartoon.js [world ...] -> slopfeeder/cartoon/<slug>.mp4 (24 fps) + keys/<slug>-NNN.png at each x-sheet row and every 24 frames
const path = require('path'), fs = require('fs'), { execFileSync } = require('child_process');
const { createCanvas } = require(path.join(process.env.HOME, 'Downloads/boots-render/node_modules/@napi-rs/canvas'));
const SC = require('./cartoon.js'), D = __dirname, O = path.join(D, 'cartoon'); fs.mkdirSync(path.join(O, 'keys'), { recursive: true });
const slug = w => w.toLowerCase().replace(/^the /, '').replace(/ /g, '-');
const only = process.argv.slice(2); const out = {};
for (const [w, shot] of Object.entries(SC.SHOTS)) {
  if (only.length && !only.some(o => slug(w).startsWith(o))) continue;
  const tmp = fs.mkdtempSync(path.join(require('os').tmpdir(), 'cart-')), cv = createCanvas(SC.W, SC.H), g = cv.getContext('2d');
  const keys = new Set([...shot.xsheet.map(r => r[0] - 1), ...Array.from({ length: Math.floor(shot.dur / 24) + 1 }, (_, k) => k * 24), shot.dur - 1]);
  for (let f = 0; f < shot.dur; f++) { g.setTransform(1, 0, 0, 1, 0, 0); SC.photograph(g, shot, f); const png = cv.toBuffer('image/png');
    fs.writeFileSync(path.join(tmp, String(f).padStart(4, '0') + '.png'), png); if (keys.has(f)) fs.writeFileSync(path.join(O, 'keys', `${slug(w)}-${String(f).padStart(3, '0')}.png`), png); }
  const mp4 = path.join(O, slug(w) + '.mp4');
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', '24', '-i', path.join(tmp, '%04d.png'), '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', mp4]);
  fs.rmSync(tmp, { recursive: true }); out[w] = { slug: slug(w), dur: shot.dur / 24, mp4: 'cartoon/' + slug(w) + '.mp4', keys: [...keys].sort((a, b) => a - b).map(f => `cartoon/keys/${slug(w)}-${String(f).padStart(3, '0')}.png`), xsheet: shot.xsheet };
  console.log(w, shot.dur, 'frames ->', mp4);
}
const J = path.join(O, 'cartoon.json'), prev = fs.existsSync(J) ? JSON.parse(fs.readFileSync(J)) : {}; fs.writeFileSync(J, JSON.stringify({ ...prev, ...out }, null, 1));
