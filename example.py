import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # Launch browser in non-headless mode
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("http://playwright.dev")
        print(await page.title())
        # Keep the browser open for a while, e.g., 10 seconds
        await asyncio.sleep(10)
        await browser.close()

asyncio.run(main())

#/Users/daniel-li/Code/browser-backend/venv/bin/python -m asyncio