#!/usr/bin/env node
/* Render the author's Halfworld pages frame by frame on her clock, for the Syzygy page's Halfworld lane.

     1. clone https://github.com/hartswf0/butterfly-halfworld and serve its root:
          cd butterfly-halfworld && python3 -m http.server 8801
     2. npm i playwright      (any Chromium; set CHROMIUM=/path/to/chrome or headless_shell)
     3. node lab/syzygy/render_halfworld.mjs [http://127.0.0.1:8801]
     4. python3 lab/syzygy/build_lanes.py

   The suite page exposes window.__hw.renderAt(t): the pages' own renderer, the same one render-film.mjs uses. Each
   poem's world.window is its span on her clock, so clock c inside a window is suite time start + (c − window[0]).
   Frames land in lab/syzygy/.halfworld-frames/<round(c × 4)>.jpg (git-ignored); existing frames are kept, so a
   stopped render resumes. */
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
const HERE = path.dirname(new URL(import.meta.url).pathname);
const OUT = path.join(HERE, ".halfworld-frames"), FPS = 4, BASE = process.argv[2] || "http://127.0.0.1:8801";
fs.mkdirSync(OUT, { recursive: true });
const b = await chromium.launch(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {});
const p = await b.newPage({ viewport: { width: 320, height: 240 }, deviceScaleFactor: 1 });
await p.goto(BASE + "/wygwyl/suite.html", { waitUntil: "load" });
await p.waitForFunction(() => window.__hw, null, { timeout: 30000 });
const films = await p.evaluate(() => window.__hw.films.map(f => [f.world.n, f.start, f.world.window]));
await p.evaluate(() => { document.body.classList.add("cinema"); const l = document.getElementById("linebar"); if (l) l.style.display = "none";
  window.dispatchEvent(new Event("resize")); if (window.__hw.halt) window.__hw.halt(); });
await p.waitForTimeout(300);
const stage = p.locator("#stage");
let n = 0;
for (const [code, start, w] of films) {
  if (!w) continue;                                   // the title film sits before her clock begins
  for (let c = w[0]; c < w[1]; c += 1 / FPS) {
    const f = path.join(OUT, String(Math.round(c * FPS)).padStart(5, "0") + ".jpg");
    if (!fs.existsSync(f)) {
      await p.evaluate(tt => window.__hw.renderAt(tt), start + (c - w[0]));
      await stage.screenshot({ path: f, type: "jpeg", quality: 72 });
    }
    if (++n % 400 === 0) console.log(code, c.toFixed(1), n);
  }
}
await b.close();
console.log("done", n, "frames");
