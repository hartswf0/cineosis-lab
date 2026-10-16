// node render.js sheet <spec>   (spec: comma list of seconds, or id:local seconds)  |  node render.js mp4
// serves nothing itself: expects http://localhost:8766/ to serve cineosis-lab/lab (python3 -m http.server 8766)
const { chromium } = require('/opt/npm-tools/node_modules/playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');
const BASE = 'http://localhost:8766/bolas/worldtext/src/film.html';
const OUT = path.resolve(__dirname, '..'), BUILD = process.env.BUILD || '/home/claude/worldtext-build';
(async () => {
  const [mode, list] = process.argv.slice(2);
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 1300, height: 740 } });
  const errs = [];
  page.on('pageerror', (e) => errs.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(BASE);
  await page.waitForFunction(() => window.__ready, null, { timeout: 30000 });
  const NF = await page.evaluate(() => window.__NF), T = await page.evaluate(() => window.__T);
  const grab = async (f) => Buffer.from((await page.evaluate(async (f) => { await window.__render(f); return document.getElementById('film').toDataURL('image/jpeg', 0.93); }, f)).split(',')[1], 'base64');
  if (mode === 'sheet') {
    const dir = path.join(BUILD, 'sheet', process.env.SD || 'x'); fs.mkdirSync(dir, { recursive: true });
    const abs = (s) => { if (!s.includes(':')) return Number(s); const [n, lt] = s.split(':'); const sc = T.scenes.find((x) => x.id === n); return sc.t0 + (lt === 'end' ? sc.d - .3 : Number(lt)); };
    for (const s of list.split(',')) { const f = Math.round(abs(s) * 24); fs.writeFileSync(path.join(dir, `s-${String(f).padStart(5, '0')}.jpg`), await grab(f)); }
    console.log('sheet done', errs.join(' | '));
  } else {
    const t0 = Date.now();
    const title = T.scenes[0], POSTER = Math.round(24 * (title.d - 1.6));
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '24', '-c:v', 'mjpeg', '-i', '-', '-i', path.join(BUILD, 'narration.m4a'),
      '-map', '0:v', '-map', '1:a', '-c:a', 'copy', '-shortest', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '24', '-preset', 'medium', '-tune', 'animation',
      '-g', '48', '-keyint_min', '24', '-movflags', '+faststart', path.join(BUILD, 'worldtext.mp4')]);
    ff.stderr.on('data', (d) => process.stderr.write(d));
    for (let f = 0; f < NF; f++) {
      const buf = await grab(f);
      if (f === POSTER) fs.writeFileSync(path.join(OUT, 'worldtext.jpg'), buf);
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
      if (f % 1200 === 0) console.log('frame', f, '/', NF, ((Date.now() - t0) / 1000).toFixed(0) + 's');
    }
    ff.stdin.end(); await new Promise((r) => ff.on('close', r));
    console.log('frames', NF, 'sec', ((Date.now() - t0) / 1000).toFixed(0), errs.length ? 'ERR ' + errs.slice(0, 3).join(' | ') : 'no errors');
  }
  await browser.close();
})();
