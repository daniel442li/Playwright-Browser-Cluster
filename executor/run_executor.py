from fastapi import WebSocket
from shared import sessions
import json
import time 
from executor.tts import text_to_speech_instant
class ExecutorWebsocket:
    def __init__(self, websocket: WebSocket, id: str):
        print(sessions)
        self.websocket = websocket
        self.browser = sessions[str(id)]

    async def connect(self):
        await self.websocket.accept()

    async def receive_and_send(self):
        while True:
            data = await self.websocket.receive_text()
            await self.websocket.send_text(f"Message text was: {data}, from ws2")
            await self.handle_action(data)
    
    async def handle_action(self, data):
        print(data)
        data = json.loads(data)
        action = data.get("action")
        print(action)
        action_handlers = {
            'new_page': self.new_page,
            'run_script': self.run_script,
        }
        if action in action_handlers:
            returned_value = await action_handlers[action](data)
            return returned_value
        else:
            await self.websocket.send_text("Error: Invalid action.")

    async def new_page(self, data):
        print("new page")
        link = data.get("link")
        page = await self.browser.new_page(link)
        await self.insert_text(page, "Opening new page.")
        return page
    

    async def edit_text(self, page, text):
        js_code_update = f"""
        document.getElementById('workman_status').innerText = "{text}";
        """
        await page.evaluate(js_code_update)
    

    async def insert_text(self, page, text):
        # JavaScript code to create and style the text container
        js_code = f"""
        var textContainer = document.createElement('div');
        textContainer.id = 'workman_status';
        textContainer.style.position = 'fixed';
        textContainer.style.bottom = '20px';
        textContainer.style.left = '50%';
        textContainer.style.transform = 'translateX(-50%)';
        textContainer.style.display = 'flex';
        textContainer.style.alignItems = 'center';
        textContainer.style.justifyContent = 'center';
        textContainer.style.width = '350px';
        textContainer.style.height = '50px';
        textContainer.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        textContainer.style.border = '3px solid black';
        textContainer.style.borderRadius = '50px';
        textContainer.style.color = 'white';
        textContainer.style.fontSize = '16px';
        textContainer.style.textAlign = 'center';
        textContainer.style.padding = '10px';
        textContainer.innerText = "{text}";
        document.body.appendChild(textContainer);
        """

        # Execute the JavaScript code in the page context
        await page.evaluate(js_code)

    async def run_script(self, data):
        new_page_data = {
            "action": "new_page",
            "link": "https://www.linkedin.com/sales/search/people?query=(recentSearchParam%3A(id%3A3281715642%2CdoLogHistory%3Atrue)%2Cfilters%3AList((type%3ACOMPANY_HEADCOUNT%2Cvalues%3AList((id%3AB%2Ctext%3A1-10%2CselectionType%3AINCLUDED)))%2C(type%3ALEAD_INTERACTIONS%2Cvalues%3AList((id%3ALIVP%2Ctext%3AViewed%2520profile%2CselectionType%3AEXCLUDED)))%2C(type%3AFUNCTION%2Cvalues%3AList((id%3A25%2Ctext%3ASales%2CselectionType%3AINCLUDED)))%2C(type%3ASENIORITY_LEVEL%2Cvalues%3AList((id%3A310%2Ctext%3ACXO%2CselectionType%3AINCLUDED)))))&sessionId=GXzxjd0QQESuJBnLds3i9A%3D%3D"
        }



        linkedin_page = await self.handle_action(json.dumps(new_page_data))


        time.sleep(3)
        
        while True:
            await linkedin_page.evaluate("""() => {
            return 'JavaScript injected successfully!';
            }""")
            if linkedin_page.url != "https://www.linkedin.com/sales/login":
                break
            await self.edit_text(linkedin_page, "I am stuck on the login page. Please login.")
            text_to_speech_instant("I am stuck on the login page. Please login.")
            
            time.sleep(5)
            print(linkedin_page.url)
        
        print(linkedin_page.url)
        print('we out the mud')

    

    
