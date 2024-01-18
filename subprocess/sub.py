import asyncio
from playwright.async_api import async_playwright
import hashlib
import httpx
import json 
import time
import janus
from nlp_parser import ai_command 
import re


def remove_extra_eol(text):
    # Replace EOL symbols
    text = text.replace('\n', ' ')
    return re.sub(r'\s{2,}', ' ', text)


def get_first_line(s):
    first_line = s.split('\n')[0]
    tokens = first_line.split()
    if len(tokens) > 8:
        return ' '.join(tokens[:8]) + '...'
    else:
        return first_line
    
async def get_element_description(element, tag_name, role_value, type_value):
    '''
         Asynchronously generates a descriptive text for a web element based on its tag type.
         Handles various HTML elements like 'select', 'input', and 'textarea', extracting attributes and content relevant to accessibility and interaction.
    '''

    salient_attributes = [
        "alt",
        "aria-describedby",
        "aria-label",
        "aria-role",
        "input-checked",
        # "input-value",
        "label",
        "name",
        "option_selected",
        "placeholder",
        "readonly",
        "text-value",
        "title",
        "value",
    ]

    parent_value = "parent_node: "
    parent_locator = element.locator('xpath=..')
    num_parents = await parent_locator.count()
    if num_parents > 0:
        # only will be zero or one parent node
        parent_text = (await parent_locator.inner_text(timeout=0) or "").strip()
        if parent_text:
            parent_value += parent_text
    parent_value = remove_extra_eol(get_first_line(parent_value)).strip()
    if parent_value == "parent_node:":
        parent_value = ""
    else:
        parent_value += " "

    if tag_name == "select":
        text1 = "Selected Options: "
        text2 = ""
        text3 = " - Options: "
        text4 = ""

        text2 = await element.evaluate(
            "select => select.options[select.selectedIndex].textContent", timeout=0
        )

        if text2:
            options = await element.evaluate("select => Array.from(select.options).map(option => option.text)",
                                             timeout=0)
            text4 = " | ".join(options)

            if not text4:
                text4 = await element.text_content(timeout=0)
                if not text4:
                    text4 = await element.inner_text(timeout=0)

            return parent_value+text1 + remove_extra_eol(text2.strip()) + text3 + text4

    input_value = ""

    none_input_type = ["submit", "reset", "checkbox", "radio", "button", "file"]

    if tag_name == "input" or tag_name == "textarea":
        if role_value not in none_input_type and type_value not in none_input_type:
            text1 = "input value="
            text2 = await element.input_value(timeout=0)
            if text2:
                input_value = text1 + "\"" + text2 + "\"" + " "

    text_content = await element.text_content(timeout=0)
    text = (text_content or '').strip()
    if text:
        text = remove_extra_eol(text)
        if len(text) > 80:
            text_content_in = await element.inner_text(timeout=0)
            text_in = (text_content_in or '').strip()
            if text_in:
                return input_value + remove_extra_eol(text_in)
        else:
            return input_value + text

    # get salient_attributes
    text1 = ""
    for attr in salient_attributes:
        attribute_value = await element.get_attribute(attr, timeout=0)
        if attribute_value:
            text1 += f"{attr}=" + "\"" + attribute_value.strip() + "\"" + " "

    text = (parent_value + text1).strip()
    if text:
        return input_value + remove_extra_eol(text.strip())


    # try to get from the first child node
    first_child_locator = element.locator('xpath=./child::*[1]')

    num_childs = await first_child_locator.count()
    if num_childs>0:
        for attr in salient_attributes:
            attribute_value = await first_child_locator.get_attribute(attr, timeout=0)
            if attribute_value:
                text1 += f"{attr}=" + "\"" + attribute_value.strip() + "\"" + " "

        text = (parent_value + text1).strip()
        if text:
            return input_value + remove_extra_eol(text.strip())

    return None


async def get_element_data(element, tag_name):
    tag_name_list = ['a', 'button',
                     'input',
                     'select', 'textarea', 'adc-tab']

    # await aprint(element,tag_name)
    if await element.is_hidden(timeout=0) or await element.is_disabled(timeout=0):
        return None

    tag_head = ""
    real_tag_name = ""
    if tag_name in tag_name_list:
        tag_head = tag_name
        real_tag_name = tag_name
    else:
        real_tag_name = await element.evaluate("element => element.tagName.toLowerCase()", timeout=0)
        if real_tag_name in tag_name_list:
            # already detected
            return None
        else:
            tag_head = real_tag_name

    role_value = await element.get_attribute('role', timeout=0)
    type_value = await element.get_attribute('type', timeout=0)
    # await aprint("start to get element description",element,tag_name )
    description = await get_element_description(element, real_tag_name, role_value, type_value)
    if not description:
        return None

    rect = await element.bounding_box() or {'x': 0, 'y': 0, 'width': 0, 'height': 0}

    if role_value:
        tag_head += " role=" + "\"" + role_value + "\""
    if type_value:
        tag_head += " type=" + "\"" + type_value + "\""

    box_model = [rect['x'], rect['y'], rect['x'] + rect['width'], rect['y'] + rect['height']]
    center_point = ((box_model[0] + box_model[2]) / 2, (box_model[1] + box_model[3]) / 2)
    selector = element


    return [center_point, description, tag_head, box_model, selector, real_tag_name]


async def get_element_data(element, tag_name):
    tag_name_list = ['a', 'button',
                     'input',
                     'select', 'textarea', 'adc-tab']

    # await aprint(element,tag_name)
    if await element.is_hidden(timeout=0) or await element.is_disabled(timeout=0):
        return None

    tag_head = ""
    real_tag_name = ""
    if tag_name in tag_name_list:
        tag_head = tag_name
        real_tag_name = tag_name
    else:
        real_tag_name = await element.evaluate("element => element.tagName.toLowerCase()", timeout=0)
        if real_tag_name in tag_name_list:
            # already detected
            return None
        else:
            tag_head = real_tag_name

    role_value = await element.get_attribute('role', timeout=0)
    type_value = await element.get_attribute('type', timeout=0)
    # await aprint("start to get element description",element,tag_name )
    description = await get_element_description(element, real_tag_name, role_value, type_value)
    if not description:
        return None

    rect = await element.bounding_box() or {'x': 0, 'y': 0, 'width': 0, 'height': 0}

    if role_value:
        tag_head += " role=" + "\"" + role_value + "\""
    if type_value:
        tag_head += " type=" + "\"" + type_value + "\""

    box_model = [rect['x'], rect['y'], rect['x'] + rect['width'], rect['y'] + rect['height']]
    center_point = ((box_model[0] + box_model[2]) / 2, (box_model[1] + box_model[3]) / 2)
    selector = element


    return [center_point, description, tag_head, box_model, selector, real_tag_name]

async def get_interactive_elements_with_playwright(page):
    interactive_elements_selectors = [
        'a', 'button',
        'input',
        'select', 'textarea', 'adc-tab', '[role="button"]', '[role="radio"]', '[role="option"]', '[role="combobox"]',
        '[role="textbox"]',
        '[role="listbox"]', '[role="menu"]',
        '[type="button"]', '[type="radio"]', '[type="combobox"]', '[type="textbox"]', '[type="listbox"]',
        '[type="menu"]',
        '[tabindex]:not([tabindex="-1"])', '[contenteditable]:not([contenteditable="false"])',
        '[onclick]', '[onfocus]', '[onkeydown]', '[onkeypress]', '[onkeyup]', "[checkbox]",
        '[aria-disabled="false"],[data-link]'
    ]

    tasks = []

    seen_elements = set()
    for selector in interactive_elements_selectors:
        locator = page.locator(selector)
        element_count = await locator.count()
        for index in range(element_count):
            element = locator.nth(index)
            tag_name = selector.replace(":not([tabindex=\"-1\"])", "")
            tag_name = tag_name.replace(":not([contenteditable=\"false\"])", "")
            task = get_element_data(element, tag_name)

            tasks.append(task)

    results = await asyncio.gather(*tasks)

    interactive_elements = []
    for i in results:
        if i:
            if i[0] in seen_elements:
                continue
            else:
                seen_elements.add(i[0])
                interactive_elements.append(i)
    return interactive_elements


class BrowserAutomation:
    def __init__(self, session_id):
        self.session_id = session_id
        self.queue = janus.Queue()
        self.last_screenshot_hash = None
        self.screenshot_debounce_timer = None
        self.browser = None
        self.page = None
        self.async_queue = asyncio.Queue()

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
        await self.queue.async_q.put(command_json) 
    ### Processes Commands ###
    async def process_commands(self):
        while True:
            command_data = await self.queue.async_q.get()
            print(command_data)
            try:
                # Parse the command and its parameters from JSON
                command_name = command_data.get("command")
                parameters = command_data.get("parameters", {})

                if command_name == "exit":
                    await self.browser.close()
                    return
                elif command_name == "navigate":
                    await self.navigate(parameters)
                # Add more commands as needed
                # ...
            except json.JSONDecodeError:
                print("Invalid command format. Please use JSON format.")

            await asyncio.sleep(0.1)

    async def navigate(self, parameters):
        print("Navigating...")
        link = parameters.get("link")
        await self.page.goto(link)

    async def start(self):
        print("Starting...")
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(headless=False)
            self.page = await self.browser.new_page()

            # Add cookies to the page instance
            cookies = [{
                'name': 'li_at',
                'value': 'AQEDAStP9dYC9O6EAAABjR4PIMoAAAGNQhukylYAd6D8c3Os7HPd9ty8Pd-KvcdfVN-DB2ykjgy2NlLtZ4e5YPD1mgofKIjDm0w9zUXlxCmKBm96tKavk0-L5KtRNIMrMaWZRSq4NLtbDaPvWU6mpaY6',
                'domain': 'www.linkedin.com',
                'path': '/',
            }]
            await self.page.context.add_cookies(cookies)

            await self.page.expose_function("onCustomDOMChange", self._on_dom_change)

            observe_dom_script = """
                new MutationObserver(async () => {
                    await window.onCustomDOMChange(); // Notify Python about the DOM change
                }).observe(document, { childList: true, subtree: true });
            """

            await self.page.add_init_script(observe_dom_script)
            await self.page.goto("http://google.com")

            # Start processing commands
            await self.navigate({"link": "https://www.linkedin.com/"})
            # Additional actions can be added here

            await asyncio.sleep(50)


# Modify test_automation to use the new method
async def test_automation():
    #note: there's prob a high likelihood you are leaking memory
    session_id = "test"  # Replace with your actual session ID

    # Instantiate the BrowserAutomation object
    automation = BrowserAutomation(session_id)

    await automation.start()
    print("exiting")

    

if __name__ == "__main__":
    asyncio.run(test_automation())