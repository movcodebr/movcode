// uso: node capa.js [saida.jpg|.png]   (padrao: entrega/movcode-reels-capa.jpg)
const { chromium } = require('playwright-core');
const path = require('path');
const EXE = process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';

(async () => {
  const out = process.argv[2] || path.join(__dirname, 'entrega', 'movcode-reels-capa.jpg');
  const browser = await chromium.launch({ executablePath: EXE, args: ['--font-render-hinting=none', '--force-color-profile=srgb', '--disable-lcd-text'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => console.error('PAGEERROR', e.message));
  await page.goto('file://' + path.resolve(__dirname, 'capa.html'));
  await page.evaluate(() => window.__ready);
  const jpg = /\.jpe?g$/i.test(out);
  await page.screenshot({ path: out, type: jpg ? 'jpeg' : 'png', ...(jpg ? { quality: 92 } : {}), clip: { x: 0, y: 0, width: 1080, height: 1920 } });
  await browser.close();
  console.log(out);
})();
