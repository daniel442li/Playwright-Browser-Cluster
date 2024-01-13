const ffmpeg = require('fluent-ffmpeg');

function streamFLVVideo() {
    ffmpeg('test.flv') // Replace with the path to your test.flv file
        .format('flv')
        .addOption('-c:v', 'libx264') // Video codec
        .addOption('-c:a', 'aac') // Audio codec
        .addOption('-flvflags', 'no_duration_filesize')
        .addOption('-b:v', '1000k') // Adjust bitrate as needed
        .addOption('-preset', 'veryfast') // Adjust preset for performance
        .addOption('-r', '30') // Reduce frame rate if necessary
        .output('rtmp://localhost/live/your_stream_key') // Replace with your RTMP server URL and stream key
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
}

streamFLVVideo();
