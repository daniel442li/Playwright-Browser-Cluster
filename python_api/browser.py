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

    async def _get_index_from_option_name(self, name):
        if len(name) == 1:
            return string.ascii_uppercase.index(name)
        elif len(name) == 2:
            first_letter_index = string.ascii_uppercase.index(name[0])
            second_letter_index = string.ascii_uppercase.index(name[1])
            return 26 + first_letter_index * 26 + second_letter_index
        else:
            raise Exception("The string should be either 1 or 2 characters long")

    async def send_screenshot(self):
        # Capture a screenshot directly to memory
        screenshot_data = await self.page.screenshot(full_page=True)

        # Encode the binary data in Base64
        base64_encoded_image = base64.b64encode(screenshot_data).decode('utf-8')

        print("Sending screenshot in Base64 format")
        async with httpx.AsyncClient() as client:
            await client.post(
                f"http://localhost:8000/receive_image/{self.session_id}",
                json={"image_data": base64_encoded_image}
            )

    ### Processes Commands ###
    async def process_commands(self):
        #infinite loop so that it doesn't close
        while True:
            await asyncio.sleep(0.1)

    async def navigate_cache(self, link):
        if "." not in link:
            link += ".com"
        await self.page.goto(link)

    async def click_cache(self, frame, selector):
        my_frame = self.page.frame(url=frame)
        if my_frame:
            new_locator = my_frame.locator(selector)
        else:
            new_locator = self.page.locator(selector)

        await new_locator.evaluate("element => element.click()", timeout=10000)

    async def press_cache(self, key):
        await self.page.keyboard.press(key)

    async def search_cache(self, query, frame, selector, type_selector):
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
        future = asyncio.Future()

        async def perform_form_fill():
            gen_parameters = []
            
            elements, choices, multi_choice = await get_multi_inputs(
                self.page, "input"
            )


            selection = await answer_multiple_choice_forms(
                "All form elements", multi_choice
            )

            for input in selection:
                try:
                    answer = input["answer"]
                    element_id = await self._get_index_from_option_name(answer)
                    target_element = elements[int(choices[element_id][0])]
                    parent_node = target_element[1]
                    
                    selector = target_element[-2]

                    await selector.clear(timeout=10000)
                    await selector.fill("Default", timeout=10000)

                    pattern = r"parent_node: ([\w\s]+) name="
                    parent_node_text = re.search(pattern, parent_node).group(1) if re.search(pattern, parent_node) else None

                    frame_url_pattern = r"url='(.*?)'"
                    frame_url_match = re.search(frame_url_pattern, str(selector))
                    frame_url = (
                        frame_url_match.group(1) if frame_url_match else None
                    )

                    # Pattern for extracting the selector
                    selector_pattern = r"selector='(.*?)'"
                    selector_match = re.search(selector_pattern, str(selector))
                    selector = selector_match.group(1) if selector_match else None

                    gen_parameters.append([frame_url, selector, parent_node_text, "Default"])
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
        print("Starting...")
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(headless=False)
            self.page = await self.browser.new_page()

            await stealth_async(self.page)

            

            # Sends screenshot to the browser
            # await self.page.add_init_script(observe_dom_script)
            await self.page.goto("https://google.com/")
            await self.page.wait_for_load_state('load')
            # await self.page.expose_function("_sendDomChange", self.send_dom_change)

            # # Set up a mutation observer to listen to DOM changes
            # await self.page.evaluate('''() => {
            #     let debounceTimer;
            #     let aggregatedChanges = [];

            #     const debounce = (func, delay) => {
            #         clearTimeout(debounceTimer);
            #         debounceTimer = setTimeout(() => {
            #             func(aggregatedChanges.join(''));
            #             aggregatedChanges = []; // Reset the aggregated changes
            #         }, delay);
            #     };

            #     var callback = function(mutationsList, observer) {
            #         for(var mutation of mutationsList) {
            #             if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            #                 mutation.addedNodes.forEach(node => {
            #                     if (node.outerHTML) {
            #                         aggregatedChanges.push(node.outerHTML);
            #                     }
            #                 });
            #             }
            #             // Handle other types of mutations if necessary
            #         }

            #         debounce((htmlContent) => {
            #             if(htmlContent) {
            #                 console.log('Sending HTML content');
            #                 window._sendDomChange(htmlContent);
            #             }
            #         }, 1000);  // Debounce delay
            #     };

            #     var observer = new MutationObserver(callback);
            #     observer.observe(document.body, { childList: true, subtree: true });
            # }''')

            # time.sleep(5)
            # await self.send_dom_change()

            # Start processing commands

            print("Ready!")
            await self.set_ready()

            await self.send_screenshot()
            await self.process_commands()
            # Additional actions can be added here

    async def close(self):
        if self.page is not None:
            await self.page.close()
        if self.browser is not None:
            await self.browser.close()
        if self.queue is not None:
            await self.queue.async_q.put(None)  # To stop the command processing loop

    
    async def set_ready(self):
        self.ready = not self.ready

    async def set_running(self):
        self.running = not self.running

    async def set_viewed(self):
        self.isViewed = not self.isViewed
