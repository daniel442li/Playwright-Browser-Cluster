import asyncio
from playwright.async_api import async_playwright
import time
import hashlib

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        last_screenshot_hash = None
        screenshot_debounce_timer = None

        # Function to take screenshot
        async def take_screenshot():
            nonlocal last_screenshot_hash, screenshot_debounce_timer
            screenshot = await page.screenshot()
            current_hash = hashlib.md5(screenshot).hexdigest()

            if current_hash != last_screenshot_hash:
                last_screenshot_hash = current_hash
                timestamp = int(time.time())
                await page.screenshot(path=f'screenshot_{timestamp}.png')
                print(f"Screenshot taken at {timestamp}")

        async def on_dom_change():
            nonlocal screenshot_debounce_timer
            if screenshot_debounce_timer is not None:
                screenshot_debounce_timer.cancel()

            screenshot_debounce_timer = asyncio.create_task(asyncio.sleep(0.1))  # 500 milliseconds debounce
            try:
                await screenshot_debounce_timer
                await take_screenshot()
            except asyncio.CancelledError:
                pass

        # Expose the Python function to the page context
        await page.expose_function("onCustomDOMChange", on_dom_change)

        # JavaScript for the MutationObserver
        observe_dom_script = """
            new MutationObserver(async () => {
                await window.onCustomDOMChange(); // Notify Python about the DOM change
            }).observe(document, { childList: true, subtree: true });
        """

        # Inject the MutationObserver script
        await page.add_init_script(observe_dom_script)

        # Perform the main actions
        await page.goto("http://google.com")
        await page.type('#APjFqb', 'Hello, World!', delay=100)

        # Wait for a while to observe DOM changes
        await asyncio.sleep(120)

        await browser.close()

asyncio.run(main())
