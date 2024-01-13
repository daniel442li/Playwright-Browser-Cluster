const puppeteer = require('puppeteer');

async function takeScreenshots() {
    const browser = await puppeteer.launch({ executablePath: '/Applications/Chromium.app/Contents/MacOS/Chromium', headless: false });
    const page = await browser.newPage();
    await page.goto('https://youtube.com');

    // Set an interval for taking screenshots
    setInterval(async () => {
        await page.screenshot({ path: 'screenshot.png' });
        // You can also save screenshots with a timestamp or unique identifier
    }, 50); // Adjust the interval as needed

    // Don't forget to close the browser when done
    // await browser.close();
}

takeScreenshots();
