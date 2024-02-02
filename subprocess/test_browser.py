import asyncio
from playwright.async_api import async_playwright
import hashlib
import httpx
import json 
import time
import janus
from nlp_parser import ai_command 
from multi_choice import get_multi_inputs
import string
from selection import convert 
import re

async def get_index_from_option_name(name):
    if len(name) == 1:
        return string.ascii_uppercase.index(name)
    elif len(name) == 2:
        first_letter_index = string.ascii_uppercase.index(name[0])
        second_letter_index = string.ascii_uppercase.index(name[1])
        return 26 + first_letter_index * 26 + second_letter_index
    else:
        raise Exception("The string should be either 1 or 2 characters long")
    

class BrowserAutomation:
    def __init__(self, session_id):
        self.session_id = session_id
        self.queue = janus.Queue()
        self.last_screenshot_hash = None
        self.screenshot_debounce_timer = None
        self.browser = None
        self.page = None
        self.async_queue = asyncio.Queue()

    async def _take_and_send_screenshot(self):
        screenshot = await self.page.screenshot()
        current_hash = hashlib.md5(screenshot).hexdigest()

        if current_hash != self.last_screenshot_hash:
            self.last_screenshot_hash = current_hash
            async with httpx.AsyncClient() as client:
                await client.post(f"http://localhost:8000/receive_screenshot/{self.session_id}", files={"file": screenshot})

    async def _on_dom_change(self):
        if self.screenshot_debounce_timer is not None:
            self.screenshot_debounce_timer.cancel()

        self.screenshot_debounce_timer = asyncio.create_task(asyncio.sleep(0.1))  # Debounce for 100 milliseconds
        try:
            await self.screenshot_debounce_timer
            await self._take_and_send_screenshot()
        except asyncio.CancelledError:
            pass
    

    # Asynchronous method to add commands to the queue
    async def add_command_async(self, command_json):
        await self.queue.async_q.put(command_json) 
    ### Processes Commands ###

    async def process_commands(self):
        while True:
            command_data = await self.queue.async_q.get()
            print(command_data)
            try:
                # Parse the command and its parameters from JSON
                command_name = command_data.get("command")
                parameters = command_data.get("parameters", {})

                if command_name == "exit":
                    await self.browser.close()
                    return
                elif command_name == "navigate":
                    await self.navigate(parameters)
                elif command_name == "search":
                    await self.search(parameters)
                
            except json.JSONDecodeError:
                print("Invalid command format. Please use JSON format.")

            await asyncio.sleep(0.1)

    async def navigate(self, parameters):
        link = parameters.get("link")
        await self.page.goto(link)

    async def search(self, parameters): 
        query = parameters.get("query")
        # Assuming there's a function to find the search input element, replace with actual function if available
        elements, choices, multi_choice = await get_multi_inputs(self.page)
        selection = convert("Search bar", multi_choice)

        element_id = get_index_from_option_name(selection)

        target_element = elements[int(choices[element_id][0])]
        selector = target_element[-2]

        await selector.clear(timeout=10000)
        await selector.fill("", timeout=10000)
        await selector.press_sequentially(query, timeout=10000)

        # element_id = "test.py"
        # element_id = get_index_from_option_name(element_id)

        # #ahhhh
        # target_element = choices[element_id][1]
        # selector = target_element[-2]
        # await selector.clear(timeout=10000)
        # await selector.fill("", timeout=10000)
        # await selector.press_sequentially("hello", timeout=10000)

        

    async def start(self):
        print("Starting...")
        async with async_playwright() as p:
            #self.browser = await p.chromium.launch(headless=False)
            self.browser = await p.chromium.launch()

            self.page = await self.browser.new_page()

            # Add cookies to the page instance
            cookies = [{
                'name': 'li_at',
                'value': 'AQEDAStP9dYC9O6EAAABjR4PIMoAAAGNQhukylYAd6D8c3Os7HPd9ty8Pd-KvcdfVN-DB2ykjgy2NlLtZ4e5YPD1mgofKIjDm0w9zUXlxCmKBm96tKavk0-L5KtRNIMrMaWZRSq4NLtbDaPvWU6mpaY6',
                'domain': 'www.linkedin.com',
                'path': '/',
            }]
            await self.page.context.add_cookies(cookies)

            await self.page.expose_function("onCustomDOMChange", self._on_dom_change)

            observe_dom_script = """
                new MutationObserver(async () => {
                    await window.onCustomDOMChange(); // Notify Python about the DOM change
                }).observe(document, { childList: true, subtree: true });
            """

            #await self.page.add_init_script(observe_dom_script)
            await self.page.goto("http://google.com")

            # Start processing commands
            await self.navigate({"link": "https://www.reddit.com/"})
            # Additional actions can be added here

            x = time.time()
            
            elements, choices, multi_choice = await get_multi_inputs(self.page)
            print(elements)

            pattern = r"(?:selector=')(button|input|textarea)"
            

            selection = convert("Search element", multi_choice)
            
            print(choices)
            print(multi_choice)
            print(selection)
            element_id = get_index_from_option_name(selection)
            print(element_id)

            target_element = elements[int(choices[element_id][0])]
            selector = target_element[-2]
            print(selector)

            type_selector = re.search(pattern, str(selector)).group(1)
            print(type_selector)

            if type_selector == "input":
                await selector.clear(timeout=10000)
                await selector.fill("", timeout=10000)
            elif type_selector == "button" or type_selector == 'textarea':
                await selector.evaluate("element => element.click()", timeout=10000)
            elif type_selector == "No match":
                print("No matching element type found")
            await selector.press_sequentially("lebron", timeout=10000)

            print(time.time() - x)

            
            

            await asyncio.sleep(50)


# Modify test_automation to use the new method
async def test_automation():
    #note: there's prob a high likelihood you are leaking memory
    session_id = "test"  # Replace with your actual session ID

    # Instantiate the BrowserAutomation object
    automation = BrowserAutomation(session_id)

    await automation.start()
    print("exiting")

    

if __name__ == "__main__":
    asyncio.run(test_automation())