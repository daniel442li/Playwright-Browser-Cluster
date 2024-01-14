import asyncio
from playwright.async_api import async_playwright
import time

async def take_screenshots(page, interval=0.25):
    while True:
        try:
            if page.is_closed() or await page.evaluate("document.readyState") == "complete":
                break
        except Exception as e:
            # Handle the exception if the execution context is destroyed due to navigation
            if "Execution context was destroyed" in str(e):
                # Optionally, log this event if needed
                print("Navigation in progress, retrying...")
            else:
                # If it's a different exception, re-raise it
                raise
        finally:
            # Ensure that we always wait and take a screenshot
            await asyncio.sleep(interval)
            if not page.is_closed():
                timestamp = int(time.time())
                await page.screenshot(path=f'screenshot_{timestamp}.png')

async def main(url, action):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Start the screenshot task
        screenshot_task = asyncio.create_task(take_screenshots(page))

        # Perform the main action (like page.goto)
        await action(page)

        # Wait for the screenshot task to complete
        await screenshot_task

        await browser.close()

# Example usage
async def go_to_page(page):
    await page.goto("http://playwright.dev")
    # You can add other commands here as needed

url = "http://playwright.dev"
asyncio.run(main(url, go_to_page))
