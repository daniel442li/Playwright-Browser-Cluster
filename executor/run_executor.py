from fastapi import WebSocket
from shared import sessions
import json
import time 
from executor.tts import text_to_speech_instant
from executor.label import workman_id_generator
class ExecutorWebsocket:
    def __init__(self, websocket: WebSocket, id: str):
        print(sessions)
        self.websocket = websocket
        self.browser = sessions[str(id)]
        self._current_tf_id = 0
    
    def _get_modify_dom_and_update_current_tf_id_js_code(self):
        """Returns the JavaScript code that is used to modify the DOM adn return the updated current_tf_id."""
        # Future scope: Move to a js file, read it and return it
        return workman_id_generator

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
        await self.edit_text(page, "Opening new page.")
        return page
    

    async def edit_text(self, page, text):
        js_code_check_and_update = f"""
        var statusElement = document.getElementById('workman_status');
        if (statusElement) {{
            statusElement.innerText = "{text}";
        }} else {{
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
        }}
        """
        await page.evaluate(js_code_check_and_update)
    
    async def check_login(self, page, login_page):
        while True:
            try:
                await page.evaluate("""() => {
                return 'so the page loads dynamically!';
                }""")
            except:
                pass

            if page.url != login_page:
                break
            await self.edit_text(page, "I am stuck on the login page. Please login.")
            text_to_speech_instant("I am stuck on the login page. Please login.")
            
            time.sleep(5)
            print(page.url)

    async def load_all_content(self, page):
        await self.edit_text(page, "I will now scan the whole site.")
        text_to_speech_instant("I will now scan the whole site.")

        # Press Tab once to focus on the first focusable element
        await page.keyboard.press('Tab')

        # Get the rectangle of the first focused element
        first_rect = await page.evaluate("""() => {
            const element = document.activeElement;
            const rect = element.getBoundingClientRect();
            return {x: rect.left + window.scrollX, y: rect.top + window.scrollY};
        }""")

        print("First element:", first_rect)

        while True:
            # Press Tab to focus on the next element
            await page.keyboard.press('Tab')
            # Optionally, add a small delay between each press to simulate more natural behavior
            await page.wait_for_timeout(5)  # Wait for 50 milliseconds

            # Get the rectangle of the currently focused element
            current_rect = await page.evaluate("""() => {
                const element = document.activeElement;
                const rect = element.getBoundingClientRect();
                return {x: rect.left + window.scrollX, y: rect.top + window.scrollY};
            }""")

            # Log the x and y coordinates
            #print(f"Focused element is at x: {current_rect['x']}, y: {current_rect['y']}")

            # Check if the current element's rect matches the first element's rect
            if current_rect == first_rect:
                await self.edit_text(page, "Scanning complete.")
                text_to_speech_instant("Scanning complete.")
                break
    
    async def load_accessibility_tree(self, page):
        self._current_tf_id = 0
        self._current_tf_id = await page.evaluate(
            self._get_modify_dom_and_update_current_tf_id_js_code(),
            {"current_tf_id": self._current_tf_id},
        )

    async def run_script(self, data):
        new_page_data = {
            "action": "new_page",
            "link": "https://www.linkedin.com/sales/search/people?query=(recentSearchParam%3A(id%3A3281715642%2CdoLogHistory%3Atrue)%2Cfilters%3AList((type%3ACOMPANY_HEADCOUNT%2Cvalues%3AList((id%3AB%2Ctext%3A1-10%2CselectionType%3AINCLUDED)))%2C(type%3ALEAD_INTERACTIONS%2Cvalues%3AList((id%3ALIVP%2Ctext%3AViewed%2520profile%2CselectionType%3AEXCLUDED)))%2C(type%3AFUNCTION%2Cvalues%3AList((id%3A25%2Ctext%3ASales%2CselectionType%3AINCLUDED)))%2C(type%3ASENIORITY_LEVEL%2Cvalues%3AList((id%3A310%2Ctext%3ACXO%2CselectionType%3AINCLUDED)))))&sessionId=GXzxjd0QQESuJBnLds3i9A%3D%3D"
        }



        linkedin_page = await self.handle_action(json.dumps(new_page_data))


        time.sleep(3)
        
        await self.check_login(linkedin_page, "https://www.linkedin.com/sales/login")
        
        
        time.sleep(5)

        #pages = await self.browser.pages()
        #current_page = pages[-1]  # Gets the most recently opened page
        #print(current_page.url)
        await self.load_all_content(linkedin_page)




    

    
