from fastapi import WebSocket
from shared import sessions
class ExecutorWebsocket:
    def __init__(self, websocket: WebSocket, id: str):
        self.websocket = websocket
        self.browser = sessions[id]

    async def connect(self):
        await self.websocket.accept()

    async def receive_and_send(self):
        while True:
            data = await self.websocket.receive_text()
            await self.websocket.send_text(f"Message text was: {data}, from ws2")
    

    
