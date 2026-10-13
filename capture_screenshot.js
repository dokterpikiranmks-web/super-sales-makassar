const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  await page.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
  await page.goto('https://frontend-murex-seven-97.vercel.app', { waitUntil: 'networkidle2' });
  await page.screenshot({ path: 'mobile_screenshot.png' });
  await browser.close();
  console.log('SCREENSHOT_SUCCESS');
})();
