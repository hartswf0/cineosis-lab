/* ATLAS FRAMES · every page of the lab filmed as a short strip of frames, so a page can be found by how it looks and moves.
   For each page in lab/atlas.json: four frames at 0.7 s, 3 s, 6 s and 10 s after it opens (if the page has a start or play
   button, it is pressed just before the second frame: the film the visitor would steer into), plus the words it shows.
   Writes lab/atlas/frames/<slug>-<0..3>.jpg (320 x 200) and lab/atlas/frames.json. Throwaway browser profile; sound muted.
   usage: node lab/atlas/frames.cjs <repo> <base-url>   e.g. node lab/atlas/frames.cjs ~/cineosis-lab http://localhost:8791 */
const path = require('path'), fs = require('fs'), os = require('os');
let puppeteer; try { puppeteer = require('puppeteer-core'); } catch (e) { puppeteer = require(path.join(os.homedir(), 'node_modules/puppeteer-core')); }
const [repo = path.join(os.homedir(), 'cineosis-lab'), base = 'http://localhost:8791', only = ''] = process.argv.slice(2);
const A = JSON.parse(fs.readFileSync(path.join(repo, 'lab/atlas.json'), 'utf8')), OUT = path.join(repo, 'lab/atlas/frames'); fs.mkdirSync(OUT, { recursive: true });
const slug = p => p.replace(/\.html$/, '').replace(/[^\w-]+/g, '__');
const TIMES = [700, 3000, 6000, 10000];
const within = (pr, ms, v) => Promise.race([pr, new Promise(r => setTimeout(() => r(v), ms))]);   // heavy pages can stall a screenshot: never wait more than ms
(async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'atlas-'));
  const b = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new', userDataDir: dir,
    args: ['--mute-audio', '--autoplay-policy=no-user-gesture-required', '--hide-scrollbars'] });
  const have = p => [0, 1, 2, 3].every(k => fs.existsSync(path.join(OUT, `${slug(p.path)}-${k}.jpg`)));
  const pages = A.pages.filter(p => only ? only.split(',').some(o => p.path.includes(o)) : !have(p) || process.env.ALL), meta = {}; let i = 0;
  const prevFile = path.join(OUT, '../frames.json');
  const prev = fs.existsSync(path.join(OUT, '../frames.json')) ? JSON.parse(fs.readFileSync(path.join(OUT, '../frames.json'), 'utf8')) : {};
  async function one(p) {
    const pg = await b.newPage(); await pg.setViewport({ width: 1280, height: 800, deviceScaleFactor: .25 }); const t0 = Date.now(), shots = []; let pressed = false, err = '';
    const press = () => pg.evaluate(() => { const c = document.querySelector('#start, [data-start], .start, button.play, #play');
      const byText = [...document.querySelectorAll('button, a.btn, [role=button], b')].find(e => /^\s*(▶|►)?\s*(watch|play|start|begin|enter|press play)\b/i.test(e.textContent || ''));
      const el = c || byText; if (el && el.getClientRects().length) { el.click(); return true; } return false; }).catch(() => false);
    try {
      await pg.goto(`${base}/${p.path}`, { waitUntil: 'domcontentloaded', timeout: 15000 }).catch(e => { err = 'slow: ' + String(e.message).slice(0, 60); });   // a slow page is still filmed: what it shows while loading is a frame too
      for (const [k, t] of TIMES.entries()) {
        const w = t - (Date.now() - t0); if (w > 0) await new Promise(r => setTimeout(r, w));
        if (k === 1) { pressed = await press(); if (pressed) await new Promise(r => setTimeout(r, 800)); }
        const f = path.join(OUT, `${slug(p.path)}-${k}.jpg`); const ok = await within(pg.screenshot({ path: f, type: 'jpeg', quality: 62, optimizeForSpeed: true }).then(() => true), 9000, false); if (ok) shots.push(path.basename(f)); else break;
      }
      meta[p.path] = { frames: shots, pressed, text: (await within(pg.evaluate(() => (document.body?.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 2400)).catch(() => ''), 4000, '')) };
    } catch (e) { err = String(e.message || e).slice(0, 120); meta[p.path] = { frames: shots, pressed, text: prev[p.path]?.text || '', err }; }
    await within(pg.close().catch(() => { }), 4000); i++; if (i % 10 === 0 || err) { console.log(i, '/', pages.length, p.path, err); fs.writeFileSync(prevFile, JSON.stringify(Object.assign({}, prev, meta))); }
  }
  const q = [...pages]; await Promise.all([...Array(6)].map(async () => { while (q.length) await one(q.shift()); }));
  fs.writeFileSync(path.join(OUT, '../frames.json'), JSON.stringify(Object.assign(prev, meta)));
  console.log('done', Object.keys(meta).length, 'pages,', Object.values(meta).reduce((s, m) => s + m.frames.length, 0), 'frames,', Object.values(meta).filter(m => m.pressed).length, 'pressed play');
  await b.close(); fs.rmSync(dir, { recursive: true, force: true });
})();
