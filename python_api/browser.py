import asyncio
from playwright.async_api import async_playwright
import hashlib
import httpx
import json 
import time
import janus
from gpt_commands import ai_command 

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
            try:
                # Parse the command and its parameters from JSON
                command_name = command_data.get("command")
                parameters = command_data.get("parameters", {})

                if command_name == "exit":
                    await self.browser.close()
                    return
                elif command_name == "navigate":
                    await self.navigate(parameters)
                # Add more commands as needed
                # ...
            except json.JSONDecodeError:
                print("Invalid command format. Please use JSON format.")

            await asyncio.sleep(0.1)

    async def navigate(self, parameters):
        link = parameters.get("link")
        await self.page.goto(link)

    async def start(self):
        print("Starting...")
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(headless=False)
            self.page = await self.browser.new_page()
            await self.page.expose_function("onCustomDOMChange", self._on_dom_change)

            observe_dom_script = """
                new MutationObserver(async () => {
                    await window.onCustomDOMChange(); // Notify Python about the DOM change
                }).observe(document, { childList: true, subtree: true });
            """

            await self.page.add_init_script(observe_dom_script)
            await self.page.goto("http://google.com")

            # Start processing commands
            await self.process_commands()
            # Additional actions can be added here