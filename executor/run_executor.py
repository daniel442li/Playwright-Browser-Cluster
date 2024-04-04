from fastapi import WebSocket
from shared import sessions
import json
import time 
from executor.tts import text_to_speech_instant
from executor.label import workman_id_generator
from executor.element_find import process_elements_links_manual, process_elements_button_manual
from executor.schemas import *

class ExecutorWebsocket:
    def __init__(self, websocket: WebSocket, id: str):
        print(sessions)
        self.websocket = websocket
        self.browser = sessions[str(id)]
        self._current_tf_id = 0
    
    def _get_modify_dom_and_update_current_tf_id_js_code(self):
        """Returns the JavaScript code that is used to modify the DOM adn return the updated current_tf_id."""
        # Future scope: Move to a js file, read it and return it
        return workman_id_generator
    
    async def get_accessibility_tree(self, page, interesting=True):
        snapshot = await page.accessibility.snapshot(interesting_only=True)
        return snapshot

    async def connect(self):
        await self.websocket.accept()

    async def receive_and_send(self):
        while True:
            data = await self.websocket.receive_text()
            await self.websocket.send_text(f"Message text was: {data}, from ws2")
            await self.handle_action(data)
    
    async def handle_action(self, data):
        print(data)
        data = json.loads(data)
        action = data.get("action")
        print(action)
        action_handlers = {
            'new_page': self.new_page,
            'run_script': self.run_script,
        }
        if action in action_handlers:
            returned_value = await action_handlers[action](data)
            return returned_value
        else:
            await self.websocket.send_text("Error: Invalid action.")

    async def new_page(self, data):
        print("new page")
        link = data.get("link")
        page = await self.browser.new_page(link)
        await self.edit_text(page, "Opening new page.")
        text_to_speech_instant("Opening new page.")
        return page
    

    async def edit_text(self, page, text):
        js_code_check_and_update = f"""
        var statusElement = document.getElementById('workman_status');
        if (statusElement) {{
            statusElement.innerText = "{text}";
        }} else {{
            var textContainer = document.createElement('div');
            textContainer.id = 'workman_status';
            textContainer.style.position = 'fixed';
            textContainer.style.bottom = '20px';
            textContainer.style.left = '50%';
            textContainer.style.transform = 'translateX(-50%)';
            textContainer.style.display = 'flex';
            textContainer.style.alignItems = 'center';
            textContainer.style.justifyContent = 'center';
            textContainer.style.width = '350px';
            textContainer.style.height = '50px';
            textContainer.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
            textContainer.style.border = '3px solid black';
            textContainer.style.borderRadius = '50px';
            textContainer.style.color = 'white';
            textContainer.style.fontSize = '16px';
            textContainer.style.textAlign = 'center';
            textContainer.style.zIndex = '1000';
            textContainer.style.padding = '10px';
            textContainer.innerText = "{text}";
            document.body.appendChild(textContainer);
        }}
        """
        await page.evaluate(js_code_check_and_update)
    
    async def check_login(self, page, login_page_selector):
        while True:
            try:
                await page.evaluate("""() => {
                return 'so the page loads dynamically!';
                }""")
            except:
                pass

            if login_page_selector in page.url:
                await self.edit_text(page, "I am stuck on the login page. Please login.")
                text_to_speech_instant("I am stuck on the login page. Please login.")
            else:
                break

            
            time.sleep(5)
            print(page.url)

    async def load_all_content(self, page):
        await self.edit_text(page, "I will now scan the whole site.")
        text_to_speech_instant("I will now scan the whole site.")

        # Press Tab once to focus on the first focusable element
        await page.keyboard.press('Tab')

        # Get the rectangle of the first focused element
        first_rect = await page.evaluate("""() => {
            const element = document.activeElement;
            const rect = element.getBoundingClientRect();
            return {x: rect.left + window.scrollX, y: rect.top + window.scrollY};
        }""")

        print("First element:", first_rect)

        await page.wait_for_timeout(5)

        await page.keyboard.press('Tab')

        # Get the rectangle of the first focused element
        second_rect = await page.evaluate("""() => {
            const element = document.activeElement;
            const rect = element.getBoundingClientRect();
            return {x: rect.left + window.scrollX, y: rect.top + window.scrollY};
        }""")



        while True:
            # Press Tab to focus on the next element
            await page.keyboard.press('Tab')
            # Optionally, add a small delay between each press to simulate more natural behavior
            await page.wait_for_timeout(5)  # Wait for 50 milliseconds

            # Get the rectangle of the currently focused element
            current_rect = await page.evaluate("""() => {
                const element = document.activeElement;
                const rect = element.getBoundingClientRect();
                return {x: rect.left + window.scrollX, y: rect.top + window.scrollY};
            }""")

            if current_rect['x'] < 50 and current_rect['y'] < 50:
                print("Current element with x and y less than 50:", current_rect)

            # Check if the current element's rect matches the first element's rect
            if (abs(current_rect['x'] - first_rect['x']) <= 2 and abs(current_rect['y'] - first_rect['y']) <= 2) or (abs(current_rect['x'] - second_rect['x']) <= 2 and abs(current_rect['y'] - second_rect['y']) <= 2):
                await self.edit_text(page, "Scanning complete.")
                text_to_speech_instant("Scanning complete.")
                break
    
    async def load_accessibility_tree(self, page):
        self._current_tf_id = await page.evaluate(
            self._get_modify_dom_and_update_current_tf_id_js_code(),
            {"current_tf_id": self._current_tf_id},
        )

    async def sort_by_y_remove_dupes(self, page, links):
        accounts = []
        for link in links:
            workman_id = json.loads(link["keyshortcuts"])["workman_id"]
            name = link["name"]
            found_element = page.locator(f'[workman_id="{workman_id}"]')
            element_coordinates = await found_element.bounding_box()
            accounts.append({
                "name": name,
                "workman_id": workman_id,
                "x": element_coordinates['x'],
                "y": element_coordinates['y']
            })

        # Sort accounts by the Y coordinate
        accounts.sort(key=lambda account: account['y'])

        filtered_accounts = []
        threshold = 5  # Define a threshold for y-coordinate difference
        for i, account in enumerate(accounts):
            if i == 0:
                filtered_accounts.append(account)
            else:
                if abs(account['y'] - filtered_accounts[-1]['y']) > threshold:
                    filtered_accounts.append(account)
        accounts = filtered_accounts

        accounts = [account for account in accounts if "Go to" in account["name"]]

        return accounts

    async def open_new_page_and_focus(self, page, element):
        found_element = page.locator(f'[workman_id="{element["workman_id"]}"]')
        print("Account: " + element["workman_id"])
        await found_element.highlight()
        await found_element.scroll_into_view_if_needed()
        
        await self.edit_text(page, f"Opening link in new tab: {element['name']}")
        text_to_speech_instant(f"Opening link in new tab: {element['name']}")

        async with page.context.expect_page() as new_page_info:
            try:
                await found_element.click(button='middle')
            except Exception as e:
                print(f"Failed to click on the element: {e}")
                return
            new_page = await new_page_info.value
            await new_page.bring_to_front()
            await self.edit_text(page, f"Opened a new page")
            text_to_speech_instant(f"Opened a new page")

        return new_page

    async def filter_elements(self, elements, filter):
        return [element for element in elements if filter in element["name"]]

    async def click_button_based_on_selector(self, page, filter, exact=False):
        await self.edit_text(page, f"Clicking on the {filter} button")
        text_to_speech_instant(f"Clicking on the {filter} button")

        await self.load_accessibility_tree(page)
        tree = await self.get_accessibility_tree(page)

        with open("tree.json", "w") as f:
            json.dump(tree, f)
        buttons = process_elements_button_manual(tree)

        try:
            if exact:
                target_id = next(json.loads(element["keyshortcuts"])["workman_id"] for element in buttons if element["name"] == filter)
            else:
                target_id = next(json.loads(element["keyshortcuts"])["workman_id"] for element in buttons if filter in element["name"])
            print(f"Target ID: {target_id}")
            target_element = page.locator(f'[workman_id="{target_id}"]')
        except StopIteration:
            print(f"No element found with filter: {filter}")
            return None

        try:
            await target_element.highlight()
            await target_element.scroll_into_view_if_needed()
        except:
            pass

        try:
            time.sleep(1)
            await target_element.click()
            return "Success"
        except:
            await page.close()
    

    async def click_link_based_on_selector(self, page, filter, exact=False):
        await self.load_accessibility_tree(page)
        tree = await self.get_accessibility_tree(page)
        links = process_elements_links_manual(tree)
        await self.edit_text(page, f"Clicking on the {filter} button")
        text_to_speech_instant(f"Clicking on the {filter} button")
        try:
            if exact:
                target_id = next(json.loads(element["keyshortcuts"])["workman_id"] for element in links if element["name"] == filter)
            else:
                target_id = next(json.loads(element["keyshortcuts"])["workman_id"] for element in links if filter in element["name"])
            print(f"Target ID: {target_id}")
            target_element = page.locator(f'[workman_id="{target_id}"]')
        except StopIteration:
            print(f"No element found with filter: {filter}")
            return None

        try:
            await target_element.highlight()
            await target_element.scroll_into_view_if_needed()
        except:
            pass

        try:
            time.sleep(1)
            new_page_future = page.context.wait_for_event('page')
            await target_element.click()

            new_page = await new_page_future
            await new_page.bring_to_front()
            return new_page
        except:
            await page.close()
    
    async def scrape_information(self, page, selector):
        try:
            element_by_class = page.locator(selector).first
            information = await element_by_class.text_content()
            return information
        except:
            return ''
        
    async def speak_information(self, page, information):
        await self.edit_text(page, information)
        text_to_speech_instant(information)

                    
    async def run_script(self, data):
        new_page_data_notion = {
            "action": "new_page",
            "link": "https://www.notion.so/9f7c1f0e5d0641bdb8e53ba28c064b5b?v=f386299c773e417bb424d585bb13af82"
        }

        new_page_data = {
            "action": "new_page",
            "link": "https://www.linkedin.com/sales/search/people?query=(recentSearchParam%3A(id%3A3281715642%2CdoLogHistory%3Atrue)%2Cfilters%3AList((type%3ACOMPANY_HEADCOUNT%2Cvalues%3AList((id%3AB%2Ctext%3A1-10%2CselectionType%3AINCLUDED)))%2C(type%3ALEAD_INTERACTIONS%2Cvalues%3AList((id%3ALIVP%2Ctext%3AViewed%2520profile%2CselectionType%3AEXCLUDED)))%2C(type%3AFUNCTION%2Cvalues%3AList((id%3A25%2Ctext%3ASales%2CselectionType%3AINCLUDED)))%2C(type%3ASENIORITY_LEVEL%2Cvalues%3AList((id%3A310%2Ctext%3ACXO%2CselectionType%3AINCLUDED)))))&sessionId=GXzxjd0QQESuJBnLds3i9A%3D%3D"
        }


        notion_page = await self.handle_action(json.dumps(new_page_data_notion))

        time.sleep(3)
        #await self.check_login(notion_page, "v=")

        
        linkedin_page = await self.handle_action(json.dumps(new_page_data))
        time.sleep(3)
        
        await self.check_login(linkedin_page, "sales/login")
        
        time.sleep(3)

        await self.load_all_content(linkedin_page)
        
        await self.load_accessibility_tree(linkedin_page)
        tree = await self.get_accessibility_tree(linkedin_page)

        links = process_elements_links_manual(tree)
        relevant_links = await self.filter_elements(links, "Go to")

        

        accounts = await self.sort_by_y_remove_dupes(linkedin_page, relevant_links)

        for account in accounts:
            profile_page = await self.open_new_page_and_focus(linkedin_page, account)

            result = await self.click_button_based_on_selector(profile_page, "Open actions")

            if not result:
                await profile_page.close()
                continue
            
            time.sleep(1)

            direct_profile_page = await self.click_link_based_on_selector(profile_page, "View LinkedIn profile")

            await linkedin_page.close()


            time.sleep(2)
            
            current_url = direct_profile_page.url
            
            name = await self.scrape_information(direct_profile_page, "h1.text-heading-xlarge.inline.t-24.v-align-middle.break-words")

            title = await self.scrape_information(direct_profile_page, ".text-body-medium.break-words")

            location = await self.scrape_information(direct_profile_page, ".text-body-small.inline.t-black--light.break-words")

            description = await self.scrape_information(direct_profile_page, "div.display-flex.ph5.pv3")


            result = await self.click_button_based_on_selector(direct_profile_page, "More actions")

            if not result:
                await direct_profile_page.close()
                continue

            result = await self.click_button_based_on_selector(direct_profile_page, "to connect")

            if not result:
                await direct_profile_page.close()
                continue

            result = await self.click_button_based_on_selector(direct_profile_page, "Add a note")

            if not result:
                await direct_profile_page.close()
                continue
            
            await self.speak_information(direct_profile_page, "I will now send a personalized message.")

            information = title + description
            user_info = user_information(information, main_schema)
            
            first_name = name_information(name)

            first_name = first_name["first_name"]

            industry = user_info["industry"].lower()
            position = user_info["position"]

            software = software_answer(industry)
            soft = software["software"]

            message = f"Hi {first_name},"
            message2 = f"We build AI digital workers."
            message3 = f"These workers are experts in {industry} and can operate software such as {soft}."  
            message4 = "We're looking for limited pilot partners."
            message5 = "Let's chat."
            message6 = "- Sent by a Sales Workman"

            await direct_profile_page.keyboard.type(message, delay=20)

            await direct_profile_page.keyboard.press('Enter')

            await direct_profile_page.keyboard.type(message2, delay=20)

            await direct_profile_page.keyboard.press('Enter')

            await direct_profile_page.keyboard.type(message3, delay=20)

            await direct_profile_page.keyboard.press('Enter')

            await direct_profile_page.keyboard.type(message4, delay=20)

            await direct_profile_page.keyboard.press('Enter')

            await direct_profile_page.keyboard.type(message5, delay=20)

            await direct_profile_page.keyboard.press('Enter')

            await direct_profile_page.keyboard.type(message6, delay=20)


            time.sleep(3)
            await notion_page.bring_to_front()
            await direct_profile_page.close()


            result = await self.click_button_based_on_selector(notion_page, "New", True) 

            


            await notion_page.keyboard.type(name, delay=20)
            time.sleep(1)
            
            await notion_page.keyboard.press('Tab')
            time.sleep(1)

            await notion_page.keyboard.type(current_url, delay=20)
            time.sleep(1)

            await notion_page.keyboard.press('Tab')
            time.sleep(1)

            print(location)
            location = location.replace("\n", "")
            location = location.strip()
            await notion_page.keyboard.type(location, delay=20)
            

            await notion_page.keyboard.press('Tab')
            time.sleep(1)

            await notion_page.keyboard.type(industry, delay=20)
            time.sleep(1)

            await notion_page.keyboard.press('Tab')

            time.sleep(1)
            await notion_page.keyboard.type(position, delay=20)

            time.sleep(1)
            await notion_page.keyboard.press('Tab')

            time.sleep(1)

            await notion_page.keyboard.type(message, delay=20)
            await notion_page.keyboard.type(' ')
            await notion_page.keyboard.type(message2, delay=20)
            await notion_page.keyboard.type(' ')
            await notion_page.keyboard.type(message3, delay=20)
            await notion_page.keyboard.type(' ')
            await notion_page.keyboard.type(message4, delay=20)
            await notion_page.keyboard.type(' ')
            await notion_page.keyboard.type(message5, delay=20)


            result = await self.click_button_based_on_selector(notion_page, "Close", False) 

            await self.speak_information(notion_page, "I have added the information to the Notion page.")

            await linkedin_page.bring_to_front()
            

            








    

    
