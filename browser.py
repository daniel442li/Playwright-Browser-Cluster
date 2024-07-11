import asyncio
from playwright.async_api import async_playwright
import json
from ai_selection.multi_choice import get_multi_inputs
import string
from ai_selection.selection import answer_multiple_choice
from ai_selection.selection import answer_multiple_choice_forms
import re
from playwright_stealth import stealth_async
from datetime import datetime, timedelta
from config import HTML_PATH
import tldextract
from urllib.parse import urlparse
import os


class BrowserAutomation:
    def __init__(self, session_id):
        self.session_id = session_id
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.ready = False
        self.running = False
        self.recorder_page = None
        self.isViewed = False
        self.cookies = []
        self.last_activity_time = datetime.now()
        self.activity_timeout_seconds = 120
        self.is_active = True
        self._current_tf_id = 0

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
            if datetime.now() - self.last_activity_time > timedelta(
                seconds=self.activity_timeout_seconds
            ):
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

        try:
            # locator = self.page.get_by_role("button", name=re.compile("Save", re.IGNORECASE))
            locator = self.page.get_by_role(
                selector, name=re.compile(frame, re.IGNORECASE)
            ).first
            await locator.hover()
            await locator.click()

        except Exception as e:
            print(f"Error: {e}")

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

    def has_valid_domain(self, url):
        extracted = tldextract.extract(url)
        # Check if the suffix (TLD) is present
        return bool(extracted.suffix)

    def has_correct_protocol(self, url, expected_protocol):
        parsed_url = urlparse(url)
        return parsed_url.scheme == expected_protocol

    async def navigate(self, passedLink):
        self.update_activity_time()
        future = asyncio.Future()

        async def load_page():
            try:
                link = passedLink

                valid_domain = self.has_valid_domain(link)

                if valid_domain:
                    has_correct_protocol = self.has_correct_protocol(link, "https")
                    if not has_correct_protocol:
                        link = "https://" + link
                else:
                    search_url = f"https://www.google.com/search?q={passedLink}"
                    link = search_url

                print(link)
                await self.page.context.add_cookies(self.cookies)

                print(self.cookies)

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

                button_text = target_element[1]

                type_selector = target_element[2]
                type_selector_pattern = r'type="([^"]*)"'
                type_selector_match = re.search(
                    type_selector_pattern, str(type_selector)
                )
                type_selector_parsed = (
                    type_selector_match.group(1) if type_selector_match else None
                )

                await selector.evaluate("element => element.click()", timeout=10000)

                frame_url_pattern = r"url='(.*?)'"
                frame_url_match = re.search(frame_url_pattern, str(selector))

                # Pattern for extracting the selector
                selector_pattern = r"selector='(.*?)'"
                selector_match = re.search(selector_pattern, str(selector))
                selector = selector_match.group(1) if selector_match else None

                cached_command = {
                    "command": "click_cache",
                    "parameters": [button_text, type_selector_parsed],
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

            elements, choices, multi_choice = await get_multi_inputs(self.page, "input")

            selection = await answer_multiple_choice_forms(multi_choice)

            count = 1
            for input in selection:
                try:

                    answer = input["answer"]
                    label = input["label"]
                    type = input["type"]
                    print(label)
                    element_id = await self._get_index_from_option_name(answer)
                    target_element = elements[int(choices[element_id][0])]
                    # parent_node = target_element[1]

                    selector = target_element[-2]

                    print(selector)

                    if type == "input":
                        await selector.clear(timeout=1000)
                        await selector.fill(str(label) + " Input", timeout=1000)

                    if type == "file":
                        await selector.set_input_files("./Resume.pdf")

                    if type == "select":
                        await selector.select_option(value=selector.first())

                    frame_url_pattern = r"url='(.*?)'"
                    frame_url_match = re.search(frame_url_pattern, str(selector))
                    frame_url = frame_url_match.group(1) if frame_url_match else None

                    # Pattern for extracting the selector
                    selector_pattern = r"selector='(.*?)'"
                    selector_match = re.search(selector_pattern, str(selector))
                    selector = selector_match.group(1) if selector_match else None

                    gen_parameters.append([frame_url, selector, label, "Default"])
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

    async def start_stream(self):
        self.update_activity_time()
        googlePage = self.page
        await self.page.goto("https://google.com/")
        if self.recorder_page is not None:
            await self.recorder_page.close()
            self.recorder_page = None

        self.recorder_page = await self.context.new_page()
        await self.recorder_page.goto(HTML_PATH + "=" + self.session_id)

    async def start(self):
        future = asyncio.Future()
        self.playwright = await async_playwright().start()

        if os.name == "nt":  # Windows
            extension_path = os.path.join(os.getcwd(), "internal-extension")
        else:
            extension_path = "./internal-extension"
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=f"./user_data_{self.session_id}",
            headless=False,
            args=[  # f'--auto-select-desktop-capture-source={self.session_id}',
                f"--auto-select-tab-capture-source-by-title=Google",
                f"--disable-extensions-except={extension_path}",
                f"--load-extension={extension_path}",
                "--enable-blink-features=AccessibilityObjectModel",
            ],
        )

        self.page = await self.context.new_page()
        await stealth_async(self.page)

        await self.page.goto("https://google.com/")
        await self.page.wait_for_load_state("load")

        self.ready = True
        self.is_active = True
        # Run the activity watchdog as a background task
        asyncio.create_task(self.activity_watchdog())

        future.set_result("Browser started")
        return future

    async def close(self):
        self.is_active = False
        self.ready = False
        if self.page is not None:
            await self.page.close()
            self.page = None
        if self.browser is not None:
            await self.browser.close()
            self.browser = None

    async def set_ready(self):
        self.ready = not self.ready

    async def set_running(self):
        self.running = not self.running

    async def set_viewed(self):
        self.isViewed = not self.isViewed

    async def coord_click(self, x, y):
        print(x, y)
        self.update_activity_time()
        future = asyncio.Future()

        async def perform_click():
            try:
                await self.page.mouse.click(x, y)
                future.set_result("Mouse clicked")
            except Exception as e:
                future.set_exception(e)

        # Schedule the click operation in the background
        asyncio.create_task(perform_click())

        # Return the future immediately
        return future

    async def hover_at_coordinates(self, x: float, y: float):
        self.update_activity_time()
        try:
            # Move the mouse to the coordinates (x, y)
            await self.page.mouse.move(x, y)
        except Exception as e:
            print(f"Error during hover: {e}")
            raise

    async def press_keys(self, key: str):
        self.update_activity_time()
        try:
            await self.page.keyboard.press(key)
        except Exception as e:
            print(f"Error during pressing keys: {e}")
            raise

    async def go_back(self):
        """Navigates one step back in the browser's history."""
        self.update_activity_time()
        try:
            await self.page.go_back()
            print("Navigated back successfully.")
        except Exception as e:
            print(f"Error navigating back: {e}")
            raise

    async def go_forward(self):
        """Navigates one step forward in the browser's history."""
        self.update_activity_time()
        try:
            await self.page.go_forward()
            print("Navigated forward successfully.")
        except Exception as e:
            print(f"Error navigating forward: {e}")
            raise

    async def scroll(self, amount: int):
        """Scrolls the page up or down based on the amount provided."""
        self.update_activity_time()
        try:
            # Execute JavaScript to scroll the window vertically by the specified amount
            # Positive amount scrolls down, negative amount scrolls up
            await self.page.evaluate(f"window.scrollBy(0, {amount});")
            print(
                f"Scrolled {'down' if amount > 0 else 'up'} by {abs(amount)} pixels successfully."
            )
        except Exception as e:
            print(f"Error during scrolling by {amount} pixels: {e}")
            raise

    async def new_page(self, link):
        self.update_activity_time()
        new_page = await self.page.context.new_page()
        await new_page.goto(link)
        return new_page
