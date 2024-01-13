const { launch, getStream } = require("puppeteer-stream");
const ffmpeg = require('fluent-ffmpeg');
const stream = require('stream');

async function startStreaming() {
    // Launching Puppeteer browser
    const browser = await launch({
        executablePath: '/Applications/Chromium.app/Contents/MacOS/Chromium',
        defaultViewport: {
            width: 1920,
            height: 1080,
        },
        headless: true,
    });

    // Opening new page and going to the video source
    const page = await browser.newPage();
    await page.goto("https://github.com/");
    await page.setViewport({
        width: 1920,
        height: 1080,
    });

    // Getting stream from Puppeteer
    const puppeteerStream = await getStream(page, {
        audio: false,
        video: true,
    });

    // puppeteerStream.on('data', (chunk) => {
    // console.log(`Received chunk of size: ${chunk.length} bytes`);
    // // Log the first few bytes of the chunk in hexadecimal
    // console.log(`First few bytes: ${chunk.slice(0, 10).toString('hex')}`);
    // });

    // Set up a PassThrough stream for FFmpeg input
    var input = new stream.PassThrough();

    // Setting up FFmpeg to convert the stream to FLV and send to RTMP server
    ffmpeg(input)
        .format('flv')
        .addOption('-c:v', 'libx264') // Video codec
        .addOption('-c:a', 'aac') // Audio codec, even if there's no audio
        .addOption('-flvflags', 'no_duration_filesize')
        .addOption('-c:v', 'libx264')
        .addOption('-b:v', '1000k') // Adjust bitrate as needed
        .addOption('-preset', 'veryfast') // Adjust preset for performance
        .addOption('-r', '30') // Reduce frame rate if necessary
        .output('rtmp://localhost/live/your_stream_key')
        .on('start', () => {
            console.log('FFmpeg process started.');
        })
        .on('end', () => {
            console.log('FFmpeg process finished.');
        })
        .on('error', (err) => {
            console.error('Error:', err);
        })
        .run();

    // Piping the puppeteerStream into the input stream for FFmpeg
    puppeteerStream.pipe(input);

    // Example: stopping the stream and browser after 30 seconds
    setTimeout(async () => {
        puppeteerStream.destroy();
        input.end();
        console.log("Streaming stopped");
    }, 60000);
}

startStreaming();
