console.log('Background!!');


let ws = new WebSocket("ws://0.0.0.0:8000/socket");

ws.onopen = () => {
    console.log('WebSocket connection established with extension');
    // You can send a message to the server after establishing the connection
    ws.send(JSON.stringify({ message: 'Connection established from extension' }));
};

ws.onmessage = (event) => {
    console.log('Message from server to extension', event.data);
};

ws.onerror = (error) => {
    console.error('WebSocket error: ', error);
};

ws.onclose = () => {
    console.log('WebSocket connection closed');
};


chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'buttonClicked') {
      console.log('Button clicked with selector:', message.selector);
      // Perform additional actions here, such as sending the selector to an external server
    }
  });
  