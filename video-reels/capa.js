// uso: node capa.js [saida.jpg|.png] [--capa <pasta>/capa.html]
// padrao: capa.html desta pasta -> entrega/movcode-reels-capa.jpg
const { chromium } = require('playwright-core');
const path = require('path');
const EXE = process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const argv = process.argv.slice(2);
const ic = argv.indexOf('--capa');
const CAPA = ic >= 0 ? path.resolve(argv.splice(ic, 2)[1]) : path.resolve(__dirname, 'capa.html');

(async () => {
  const out = argv[0] || path.join(path.dirname(CAPA), 'entrega', 'movcode-reels-capa.jpg');
  const browser = await chromium.launch({ executablePath: EXE, args: ['--font-render-hinting=none', '--force-color-profile=srgb', '--disable-lcd-text'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => console.error('PAGEERROR', e.message));
  await page.goto('file://' + CAPA);
  await page.evaluate(() => window.__ready);
  const jpg = /\.jpe?g$/i.test(out);
  await page.screenshot({ path: out, type: jpg ? 'jpeg' : 'png', ...(jpg ? { quality: 92 } : {}), clip: { x: 0, y: 0, width: 1080, height: 1920 } });
  await browser.close();
  console.log(out);
})();
