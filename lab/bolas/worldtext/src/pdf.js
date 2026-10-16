// node pdf.js -> ../worldtext.pdf: the page's print mode (one scene per page, its notes on the next), printed by Chromium
const { chromium } = require('/opt/npm-tools/node_modules/playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file://' + path.resolve(__dirname, '..', '..', 'worldtext.html') + '?print');
  await p.waitForFunction(() => document.body.dataset.printed === '1', null, { timeout: 60000 });
  await p.emulateMedia({ media: 'print' });
  await p.pdf({ path: path.resolve(__dirname, '..', 'worldtext.pdf'), width: '13.333in', height: '7.5in', printBackground: true, margin: { top: 0, bottom: 0, left: 0, right: 0 } });
  console.log('pdf done', errs.join(' | ') || 'no errors');
  await b.close();
})();
