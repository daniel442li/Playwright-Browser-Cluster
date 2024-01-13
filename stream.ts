const { launch, getStream } = require("puppeteer-stream");
const fs = require("fs");

const file = fs.createWriteStream(__dirname + "/test.webm");

async function test() {
    const browser = await launch({
        executablePath: '/Applications/Chromium.app/Contents/MacOS/Chromium',
        defaultViewport: {
            width: 1920,
            height: 1080,
        },
        headless: true,
    });

    const page = await browser.newPage();
    await page.goto("https://www.youtube.com/watch?v=HXXHzdHSlGk");
    await page.setViewport({
        width: 1920,
        height: 1080,
    });

    const stream = await getStream(page, {
        audio: false,
        video: true,
    });

    // Event listeners for the stream
    stream.on('data', (chunk) => {
        console.log(`Received chunk of size: ${chunk.length} bytes`);
        // Log the first few bytes of the chunk in hexadecimal
        console.log(`First few bytes: ${chunk.slice(0, 10).toString('hex')}`);
    });

    stream.on('end', () => {
        console.log('Stream ended.');
    });

    stream.on('error', (err) => {
        console.error('Stream encountered an error:', err);
    });

    console.log("recording");
    stream.pipe(file);

    setTimeout(() => {
        stream.destroy();
        file.end(); // Manually end the file stream
        console.log("streaming stopped");
    }, 1000 * 10);
}

test();
