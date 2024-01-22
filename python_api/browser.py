import asyncio
from playwright.async_api import async_playwright
import hashlib
import httpx
import json 
import janus
from multi_choice import get_multi_inputs
import string
from selection import answer_multiple_choice 
from selection import answer_multiple_choice_forms
import re
from playwright_stealth import stealth_async
import time

class BrowserAutomation:
    def __init__(self, session_id):
        self.session_id = session_id
        self.queue = janus.Queue()
        self.last_screenshot_hash = None
        self.screenshot_debounce_timer = None
        self.browser = None
        self.page = None
        self.async_queue = asyncio.Queue()
        self.command_list = [{}]

    async def _get_index_from_option_name(self, name):
        if len(name) == 1:
            return string.ascii_uppercase.index(name)
        elif len(name) == 2:
            first_letter_index = string.ascii_uppercase.index(name[0])
            second_letter_index = string.ascii_uppercase.index(name[1])
            return 26 + first_letter_index * 26 + second_letter_index
        else:
            raise Exception("The string should be either 1 or 2 characters long")

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
        future = asyncio.Future()
        await self.queue.async_q.put((command_json, future))
        return future

    ### Processes Commands ###
    async def process_commands(self):
        while True:
            command_data = await self.queue.async_q.get()
            if command_data is None:
             break

            command_json, future = command_data  

            try:
                # Parse the command and its parameters from JSON
                command_name = command_json.get("command")
                parameters = command_json.get("parameters", {})

                if command_name == "navigate":
                    command_future = await self.navigate(parameters)
                elif command_name == "search":
                    command_future = await self.search(parameters)
                elif command_name == "click":
                    command_future = await self.click(parameters)
                elif command_name == "press":
                    command_future = await self.press(parameters)
                elif command_name == "fill_out_form":
                    command_future = await self.fill_out_form(parameters)

                try:
                    result = await command_future
                    future.set_result(result)
                except Exception as e:
                    print(f"Error executing command {command_name}: {str(e)}")

            except json.JSONDecodeError:
                print("Invalid command format. Please use JSON format.")

            await asyncio.sleep(0.1)

    async def navigate(self, parameters):
        future = asyncio.Future()

        async def load_page():
            try:
                link = parameters.get("link")
                if '.' not in link:
                    link += '.com'
                    
                await self.page.goto(link)
                future.set_result("Navigation successful")
                
            except Exception as e:
                future.set_exception(e)

        # Schedule the page loading in the background
        asyncio.create_task(load_page())

        # Return the future immediately
        return future
    
    async def search(self, parameters):
        future = asyncio.Future()

        async def perform_search():
            try:
                query = parameters.get("query")
                elements, choices, multi_choice = await get_multi_inputs(self.page, "input")

                selection = await answer_multiple_choice("Search bar", multi_choice)

                element_id = await self._get_index_from_option_name(selection)

                target_element = elements[int(choices[element_id][0])]
                selector = target_element[-2]

                pattern = r"(?:selector=')(button|input|textarea)"
                type_selector = re.search(pattern, str(selector)).group(1)

                if type_selector == "input":
                    print("here")
                    await selector.clear(timeout=10000)
                elif type_selector == "button" or type_selector == 'textarea':
                    await selector.evaluate("element => element.click()", timeout=10000)
                    await selector.press_sequentially(query, timeout=10000)
                elif type_selector == "No match":
                    raise Exception("No matching element type found")

                await selector.press_sequentially(query, timeout=10000)
                

                
                future.set_result("Search successful")
            except Exception as e:
                future.set_exception(e)

        # Schedule the search operation in the background
        asyncio.create_task(perform_search())

        # Return the future immediately
        return future

    
    async def click(self, parameters):
        future = asyncio.Future()

        async def perform_click():
            try:
                selector = parameters.get("selector")
                elements, choices, multi_choice = await get_multi_inputs(self.page)

                selection = await answer_multiple_choice(selector, multi_choice)

                element_id = await self._get_index_from_option_name(selection)

                target_element = elements[int(choices[element_id][0])]
                selector = target_element[-2]

                await selector.evaluate("element => element.click()", timeout=10000)
                future.set_result("Click successful")
            except Exception as e:
                future.set_exception(e)

        # Schedule the click operation in the background
        asyncio.create_task(perform_click())

        # Return the future immediately
        return future

    
    async def press(self, parameters):
        future = asyncio.Future()

        async def perform_press():
            try:
                key = parameters.get("key")
                await self.page.keyboard.press(key)
                future.set_result("Key press successful")
            except Exception as e:
                future.set_exception(e)

        # Schedule the key press operation in the background
        asyncio.create_task(perform_press())

        # Return the future immediately
        return future
    

    async def fill_out_form(self, parameters):
        fields = parameters.get("fields")
        print("Filling out form")
        print(fields)

        if fields == []:
            elements, choices, multi_choice = await get_multi_inputs(self.page, "input")
            selection = await answer_multiple_choice_forms("All form elements", multi_choice)

            for input['answer'] in selection:
                element_id = await self._get_index_from_option_name(input)
                target_element = elements[int(choices[element_id][0])]
                selector = target_element[-2]
                await selector.clear(timeout=10000)
                await selector.fill("Filler", timeout=10000)

            print(selection)



    async def start(self):
        print("Starting...")
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(headless=False)
            self.page = await self.browser.new_page()

            await stealth_async(self.page)
            await self.page.expose_function("onCustomDOMChange", self._on_dom_change)

            observe_dom_script = """
                new MutationObserver(async () => {
                    await window.onCustomDOMChange(); // Notify Python about the DOM change
                }).observe(document, { childList: true, subtree: true });
            """

            #Sends screenshot to the browser
            #await self.page.add_init_script(observe_dom_script)
            await self.page.goto("http://google.com")

            # Start processing commands
            await self.process_commands()
            # Additional actions can be added here

    async def close(self):
        if self.page is not None:
            await self.page.close()
        if self.browser is not None:
            await self.browser.close()
        if self.queue is not None:
            await self.queue.async_q.put(None)  # To stop the command processing loop

