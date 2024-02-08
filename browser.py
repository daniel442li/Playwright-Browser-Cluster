import asyncio
from playwright.async_api import async_playwright
import httpx
import json
from multi_choice import get_multi_inputs
import string
from selection import answer_multiple_choice
from selection import answer_multiple_choice_forms
import re
from playwright_stealth import stealth_async
import time
import base64
from datetime import datetime, timedelta

class BrowserAutomation:
    def __init__(self, session_id):
        self.session_id = session_id
        self.last_screenshot_hash = None
        self.screenshot_debounce_timer = None
        self.browser = None
        self.page = None
        self.ready = False
        self.running = False
        self.isViewed = False
        self.cookies = []
        self.last_activity_time = datetime.now()
        self.activity_timeout_seconds = 10 
        self.is_active = True


    async def add_cookie(self, cookie):
        self.cookies.append(cookie)

    async def _get_index_from_option_name(self, name):
        if len(name) == 1:
            return string.ascii_uppercase.index(name)
        elif len(name) == 2:
            first_letter_index = string.ascii_uppercase.index(name[0])
            second_letter_index = string.ascii_uppercase.index(name[1])
            return 26 + first_letter_index * 26 + second_letter_index
        else:
            raise Exception("The string should be either 1 or 2 characters long")

    ### Processes Commands ###
    async def activity_watchdog(self):
        """Monitors for inactivity and closes the browser if the timeout is reached."""
        while True:
            await asyncio.sleep(5)  # Check every 5 seconds
            if datetime.now() - self.last_activity_time > timedelta(seconds=self.activity_timeout_seconds):
                print("Inactivity timeout reached, closing browser.")
                await self.close()
                break  # Stop the watchdog after closing the browser

    def update_activity_time(self):
        """Resets the activity timer to the current time."""
        self.last_activity_time = datetime.now()

    async def navigate_cache(self, link):
        self.update_activity_time()
        if "." not in link:
            link += ".com"
        await self.page.goto(link)

    async def click_cache(self, frame, selector):
        self.update_activity_time()
        my_frame = self.page.frame(url=frame)
        if my_frame:
            new_locator = my_frame.locator(selector)
        else:
            new_locator = self.page.locator(selector)

        await new_locator.evaluate("element => element.click()", timeout=10000)

    async def press_cache(self, key):
        self.update_activity_time()
        await self.page.keyboard.press(key)

    async def search_cache(self, query, frame, selector, type_selector):
        self.update_activity_time()
        my_frame = self.page.frame(url=frame)
        if my_frame:
            new_locator = my_frame.locator(selector)
        else:
            new_locator = self.page.locator(selector)

        if type_selector == "input":
            await new_locator.clear(timeout=10000)
        elif type_selector == "button" or type_selector == "textarea":
            await new_locator.evaluate("element => element.click()", timeout=10000)
        elif type_selector == "No match":
            raise Exception("No matching element type found")

        await new_locator.press_sequentially(query, timeout=10000)

    async def fill_out_form_cache(self, parameters):
        self.update_activity_time()
        for input in parameters:
            frame = input[0]
            selector = input[1]
            answer = input[3]

            my_frame = self.page.frame(url=frame)
            if my_frame:
                new_locator = my_frame.locator(selector)
            else:
                new_locator = self.page.locator(selector)

            await new_locator.clear(timeout=10000)
            await new_locator.fill(answer, timeout=10000)

    async def search(self, query):
        self.update_activity_time()
        future = asyncio.Future()

        async def perform_search():
            try:
                elements, choices, multi_choice = await get_multi_inputs(
                    self.page, "input"
                )

                selection = await answer_multiple_choice("Search bar", multi_choice)

                element_id = await self._get_index_from_option_name(selection)

                target_element = elements[int(choices[element_id][0])]
                selector = target_element[-2]

                pattern = r"(?:selector=')(button|input|textarea)"
                type_selector = re.search(pattern, str(selector)).group(1)

                if type_selector == "input":
                    await selector.clear(timeout=10000)
                elif type_selector == "button" or type_selector == "textarea":
                    await selector.evaluate("element => element.click()", timeout=10000)
                elif type_selector == "No match":
                    raise Exception("No matching element type found")

                await selector.press_sequentially(query, timeout=10000)

                frame_url_pattern = r"url='(.*?)'"
                frame_url_match = re.search(frame_url_pattern, str(selector))
                frame_url = frame_url_match.group(1) if frame_url_match else None

                # Pattern for extracting the selector
                selector_pattern = r"selector='(.*?)'"
                selector_match = re.search(selector_pattern, str(selector))
                selector = selector_match.group(1) if selector_match else None

                cached_command = {
                    "command": "cache_search",
                    "parameters": [query, frame_url, selector, type_selector],
                }
                future.set_result(json.dumps(cached_command))
            except Exception as e:
                future.set_exception(e)

        # Schedule the search operation in the background
        asyncio.create_task(perform_search())

        # Return the future immediately
        return future

    async def navigate(self, passedLink):
        self.update_activity_time()
        future = asyncio.Future()

        async def load_page():
            try:
                link = passedLink
                
                if not re.match(r'^[a-zA-Z]+://', link):
                    link = 'https://' + link
                
                if not re.match(r'^https?://www\.', link):
                    link = link.replace('https://', 'https://www.', 1)

                if not re.search(r'\.[a-zA-Z]{2,4}/?$', link):
                    # If not, append '.com'
                    link += '.com'
                
                
                await self.page.context.add_cookies(self.cookies)

                await self.page.goto(link)
                
                cached_command = {"command": "cache_navigate", "parameters": [link]}
                future.set_result(json.dumps(cached_command))

            except Exception as e:
                future.set_exception(e)

        # Schedule the page loading in the background
        asyncio.create_task(load_page())

        # Return the future immediately
        return future

    async def click(self, description):
        self.update_activity_time()
        future = asyncio.Future()

        async def perform_click():
            try:
                elements, choices, multi_choice = await get_multi_inputs(self.page)

                selection = await answer_multiple_choice(description, multi_choice)

                element_id = await self._get_index_from_option_name(selection)

                target_element = elements[int(choices[element_id][0])]
                selector = target_element[-2]

                await selector.evaluate("element => element.click()", timeout=10000)

                frame_url_pattern = r"url='(.*?)'"
                frame_url_match = re.search(frame_url_pattern, str(selector))
                frame_url = frame_url_match.group(1) if frame_url_match else None

                # Pattern for extracting the selector
                selector_pattern = r"selector='(.*?)'"
                selector_match = re.search(selector_pattern, str(selector))
                selector = selector_match.group(1) if selector_match else None

                cached_command = {
                    "command": "click_cache",
                    "parameters": [frame_url, selector],
                }
                future.set_result(json.dumps(cached_command))
            except Exception as e:
                future.set_exception(e)

        # Schedule the click operation in the background
        asyncio.create_task(perform_click())

        # Return the future immediately
        return future

    async def press(self, key):
        self.update_activity_time()
        future = asyncio.Future()

        async def perform_press():
            try:
                await self.page.keyboard.press(key)
                cached_command = {"command": "cache_press", "parameters": [key]}
                future.set_result(json.dumps(cached_command))
            except Exception as e:
                future.set_exception(e)

        # Schedule the key press operation in the background
        asyncio.create_task(perform_press())

        # Return the future immediately
        return future

    async def fill_out_form(self):
        self.update_activity_time()
        future = asyncio.Future()

        async def perform_form_fill():
            gen_parameters = []
            
            elements, choices, multi_choice = await get_multi_inputs(
                self.page, "input"
            )


            selection = await answer_multiple_choice_forms(
                multi_choice
            )

            count = 1
            for input in selection:
                try:
                    answer = input["answer"]
                    element_id = await self._get_index_from_option_name(answer)
                    target_element = elements[int(choices[element_id][0])]
                    #parent_node = target_element[1]
                    
                    selector = target_element[-2]

                    await selector.clear(timeout=10000)
                    await selector.fill("[FILL FORM #" + str(count) + " HERE]", timeout=10000)

                    #pattern = r"parent_node: ([\w\s]+) name="
                    #parent_node_text = re.search(pattern, parent_node).group(1) if re.search(pattern, parent_node) else None

                    frame_url_pattern = r"url='(.*?)'"
                    frame_url_match = re.search(frame_url_pattern, str(selector))
                    frame_url = (
                        frame_url_match.group(1) if frame_url_match else None
                    )

                    # Pattern for extracting the selector
                    selector_pattern = r"selector='(.*?)'"
                    selector_match = re.search(selector_pattern, str(selector))
                    selector = selector_match.group(1) if selector_match else None

                    gen_parameters.append([frame_url, selector, "Form #" + str(count), "Default"])
                    count += 1
                except Exception as e:
                    print(e)
                    pass

            cached_command = {
                "command": "fill_out_form_cache",
                "parameters": gen_parameters,
            }
            future.set_result(json.dumps(cached_command))

        asyncio.create_task(perform_form_fill())

        # Return the future immediately
        return future

    async def start(self):
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(headless=False)
            #self.browser = await p.chromium.launch()
            self.page = await self.browser.new_page()
            await stealth_async(self.page)
            await self.page.goto("https://google.com/")
            await self.page.wait_for_load_state('load')

            await self.set_ready()
            await self.activity_watchdog()

    async def close(self):
        self.is_active = False
        if self.page is not None:
            await self.page.close()
        if self.browser is not None:
            await self.browser.close()

    
    async def set_ready(self):
        self.ready = not self.ready

    async def set_running(self):
        self.running = not self.running

    async def set_viewed(self):
        self.isViewed = not self.isViewed
