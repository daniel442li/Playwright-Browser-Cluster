import asyncio
from playwright.async_api import async_playwright
import hashlib
import httpx
import time 

class BrowserAutomation:
    def __init__(self, session_id):
        self.session_id = session_id
        self.command_queue = asyncio.Queue()
        self.last_screenshot_hash = None
        self.screenshot_debounce_timer = None
        self.browser = None
        self.page = None

    async def take_and_send_screenshot(self):
        screenshot = await self.page.screenshot()
        current_hash = hashlib.md5(screenshot).hexdigest()

        if current_hash != self.last_screenshot_hash:
            self.last_screenshot_hash = current_hash
            async with httpx.AsyncClient() as client:
                await client.post(f"http://localhost:8000/receive_screenshot/{self.session_id}", files={"file": screenshot})

    async def on_dom_change(self):
        if self.screenshot_debounce_timer is not None:
            self.screenshot_debounce_timer.cancel()

        self.screenshot_debounce_timer = asyncio.create_task(asyncio.sleep(0.1))  # Debounce for 100 milliseconds
        try:
            await self.screenshot_debounce_timer
            await self.take_and_send_screenshot()
        except asyncio.CancelledError:
            pass
    
    def add_command(self, command):
        asyncio.create_task(self.command_queue.put(command))

    async def process_commands(self):
        while True:
            command = await self.command_queue.get()
            if command == "exit":
                break  # Exit the loop if the command is "exit"
            # Process other commands
            # For example, if command is a URL, then load it
            elif isinstance(command, str):  # Assuming command is a URL for simplicity
                await self.page.goto(command)
            # Add more command types and their handling logic as needed

    async def start(self):
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(headless=False)
            self.page = await self.browser.new_page()
            await self.page.expose_function("onCustomDOMChange", self.on_dom_change)

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

    async def close(self):
        await self.browser.close()


# Usage
async def main():
    automation = BrowserAutomation("test")
    await automation.start()
    # The script will continue running until an "exit" command is received

asyncio.run(main())