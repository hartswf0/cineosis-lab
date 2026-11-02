// Renders the LEGO states with three.js in headless Chromium and saves PNGs + anchors.json.
// Usage: node run.js <outDir>
const http = require('http'), fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const root = __dirname, out = path.resolve(process.argv[2] || 'renders');
fs.mkdirSync(out, { recursive: true });
const types = { '.html':'text/html', '.js':'text/javascript', '.png':'image/png' };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]);
  let f = p.startsWith('/out/') ? path.join(out, p.slice(5)) : path.join(root, p);
  fs.readFile(f, (e, d) => { if (e) { res.writeHead(404); return res.end(); } res.writeHead(200, { 'content-type': types[path.extname(f)] || 'application/octet-stream' }); res.end(d); });
}).listen(0, async () => {
  const port = server.address().port;
  let browser = await chromium.launch();
  let page = await browser.newPage();
  page.on('console', m => console.log('page:', m.text()));
  page.on('pageerror', e => console.log('pageerror:', e.message));
  await page.goto(`http://127.0.0.1:${port}/render.html`);
  await page.waitForFunction('window.ready === true', null, { timeout: 30000 });
  const DARK = '#15130f';
  const states = ['calibrate', 'target', 'lift', 'snap', 'paused', 'duplicate', 'rotate'];
  const jobs = [];
  for (const s of states) {
    jobs.push({ name: `${s}-laptop`, state: s, view: 'laptop', W: 960, H: 600, bg: DARK });
    jobs.push({ name: `${s}-bed`, state: s, view: 'plan', W: 800, H: 600, bg: DARK });
  }
  jobs.push({ name: 'beauty', state: 'beauty', view: 'beauty', W: 1600, H: 1000, bg: '#efece6' });
  const anchors = {};
  for (const j of jobs) {
    const t0 = Date.now();
    const r = await page.evaluate(a => window.renderLego(a), j);
    fs.writeFileSync(path.join(out, j.name + '.png'), Buffer.from(r.png.split(',')[1], 'base64'));
    anchors[j.name] = { W: j.W, H: j.H, anchors: r.anchors, hulls: r.hulls };
    console.log('rendered', j.name, Date.now() - t0, 'ms');
  }
  const sys = await page.evaluate(a => window.renderSystem(a), { W: 1600, H: 1000, laptopTex: '/out/lift-laptop.png', bedTex: '/out/lift-bed.png' });
  fs.writeFileSync(path.join(out, 'system.png'), Buffer.from(sys.png.split(',')[1], 'base64'));
  anchors.system = { W: 1600, H: 1000, anchors: sys.anchors, hulls: {} };
  console.log('rendered system');
  const gl = await page.evaluate(() => { const c = document.createElement('canvas').getContext('webgl2'); const d = c && c.getExtension('WEBGL_debug_renderer_info'); return d ? c.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'unknown'; });
  anchors._renderer = gl;
  fs.writeFileSync(path.join(out, 'anchors.json'), JSON.stringify(anchors, null, 1));
  console.log('GL:', gl);
  await browser.close(); server.close();
});
