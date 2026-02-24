const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();

    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', err => console.log('PAGE ERROR STR:', err.toString()));

    const fileUrl = 'file:///' + path.resolve(__dirname, 'admin.html').replace(/\\/g, '/');
    console.log('Loading:', fileUrl);

    try {
        await page.goto(fileUrl, { waitUntil: 'networkidle0' });
    } catch (e) {
        console.error('Goto error:', e);
    }

    await browser.close();
})();
