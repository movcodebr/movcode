// uso: node render.js <outDir> <fps> <from> <to> <workers>   |   node render.js --stills <outDir> t1,t2,...
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');
const EXE = process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const URL = 'file://' + path.resolve(__dirname, 'scene.html');

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => console.error('PAGEERROR', e.message));
  page.on('console', (m) => { if (m.type() === 'error') console.error('CONSOLE', m.text()); });
  await page.goto(URL);
  await page.evaluate(() => window.__ready);
  return page;
}
async function shot(page, t, file) {
  await page.evaluate((t) => window.__seek(t), t);
  await page.screenshot({ path: file, type: 'png', clip: { x: 0, y: 0, width: 1080, height: 1920 } });
}

(async () => {
  const args = process.argv.slice(2);
  const browser = await chromium.launch({ executablePath: EXE, args: ['--font-render-hinting=none', '--force-color-profile=srgb', '--disable-lcd-text'] });
  if (args[0] === '--stills') {
    const out = args[1]; fs.mkdirSync(out, { recursive: true });
    const times = args[2].split(',').map(Number);
    const page = await openPage(browser);
    for (const t of times) await shot(page, t, path.join(out, `t${t.toFixed(2).padStart(6, '0')}.png`));
    console.log(JSON.stringify(await page.evaluate(() => window.__ohole || null)));
  } else {
    const [out, fpsS, fromS, toS, wS] = args;
    const fps = +fpsS, from = +fromS, to = +toS, W = +(wS || 4);
    fs.mkdirSync(out, { recursive: true });
    const f0 = Math.round(from * fps), f1 = Math.round(to * fps);
    const total = f1 - f0;
    const per = Math.ceil(total / W);
    const t0 = Date.now();
    let done = 0;
    await Promise.all([...Array(W)].map(async (_, w) => {
      const a = f0 + w * per, b = Math.min(f1, a + per);
      if (a >= b) return;
      const page = await openPage(browser);
      for (let f = a; f < b; f++) {
        const file = path.join(out, `f${String(f).padStart(5, '0')}.png`);
        if (fs.existsSync(file)) { done++; continue; }
        await shot(page, f / fps, file);
        done++;
        if (done % 60 === 0) console.log(`${done}/${total} frames, ${((Date.now() - t0) / done).toFixed(0)} ms/frame`);
      }
    }));
    console.log(`done ${total} frames in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
  await browser.close();
})();
