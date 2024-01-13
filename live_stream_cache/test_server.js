const express = require('express');
const app = express();
const port = 3000;


app.get('/', (req, res) => {
    res.sendFile(__dirname + '/website.html'); // Serve website.html at the root route
});

app.get('/latest-screenshot', (req, res) => {
    res.sendFile(__dirname + '/screenshot.png'); // Send the latest screenshot
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
