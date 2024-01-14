from playwright.sync_api import sync_playwright
import time

def screenshot(page, name):
    page.screenshot(path=f'{name}.png')



def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()

    # Define LinkedIn cookie
    cookies = [{
        'name': 'li_at',
        'value': 'AQEDAStP9dYDmAa8AAABjQQs-DsAAAGNKDl8O04AtTnN10CX0bDxvPgQPWSD2YF7CIFVBbe5VfggjPe8z6rH7xcAHpi_XPSwLFhWa4BQlMy86Hw6Rlt0Dce5mc11WWGMZJpoIj_xcwTR7kFQJYYP_yI3',
        'domain': 'www.linkedin.com',
        'path': '/',
        # You can add other properties like 'expires', 'httpOnly', etc.
    }]

    # Add cookie to the context
    context.add_cookies(cookies)

    # Open new page
    page = context.new_page()

    # Navigate to LinkedIn
    page.goto('https://www.linkedin.com')

    # Perform your actions here
    time.sleep(10)

    # Close the browser
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
