import asyncio
from playwright.async_api import async_playwright
import time

async def take_screenshots(page, done, interval=0.2):
    while not done[0]:  # Check the done flag
        if page.is_closed():
            break

        if not page.is_closed():
            timestamp = int(time.time())
            await page.screenshot(path=f'screenshot_{timestamp}.png')

        await asyncio.sleep(interval)

async def main():
    done = [False]  # Initialize a flag to indicate when the main tasks are done
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Start the screenshot task
        screenshot_task = asyncio.create_task(take_screenshots(page, done))

        # Perform the main action (like page.goto)
        await page.goto("http://google.com")
        await page.type('#APjFqb', 'Hello, World!', delay=100)

        # Set the done flag to True to signal the screenshot task to finish
        done[0] = True
        await screenshot_task

        # Take a final screenshot if needed
        timestamp = int(time.time())
        await page.screenshot(path=f'screenshot_final_{timestamp}.png')

        await browser.close()

asyncio.run(main())
