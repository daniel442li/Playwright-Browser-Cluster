import string
import asyncio
import re


def generate_option_name(index):
    if index < 26:
        return string.ascii_uppercase[index]
    else:
        first_letter_index = (index - 26) // 26
        second_letter_index = (index - 26) % 26
        first_letter = string.ascii_uppercase[first_letter_index]
        second_letter = string.ascii_uppercase[second_letter_index]
        return f"{first_letter}{second_letter}"


def format_options(choices):
    option_text = ""
    abcd = ""

    multi_choice = ""
    for multichoice_idx, choice in enumerate(choices):
        multi_choice += f"{generate_option_name(multichoice_idx)}. {choice[1]}\n"
        abcd += f"{generate_option_name(multichoice_idx)}, "

    option_text += multi_choice + "\n\n"
    return option_text



# def format_options(choices):
#     option_text = ""
#     abcd = ""
#     non_abcd = ""

#     multi_choice = ""
#     for multichoice_idx, choice in enumerate(choices):
#         multi_choice += f"{generate_option_name(multichoice_idx)}. {choice[1]}\n"
#         abcd += f"{generate_option_name(multichoice_idx)}, "


#     multi_choice += f"{non_abcd}. None of the other options match the correct element"
#     # option_text += abcd
#     option_text += f"If none of these elements match your target element, please select {non_abcd}. None of the other options match the correct element.\n"

#     option_text += multi_choice + "\n\n"
#     return option_text


def format_choices(elements, candidate_ids):
    converted_elements = [
        f'<{element[2]} id="{i}">'
        + (
            element[1]
            if len(element[1].split()) < 30
            else " ".join(element[1].split()[:30]) + "..."
        )
        + f"</{element[-1]}>"
        if element[2] != "select"
        else f'<{element[2]} id="{i}">' + (element[1]) + f"</{element[-1]}>"
        for i, element in enumerate(elements)
    ]

    choices = [[str(i), converted_elements[i]] for i in candidate_ids]

    return choices


def remove_extra_eol(text):
    # Replace EOL symbols
    text = text.replace("\n", " ")
    return re.sub(r"\s{2,}", " ", text)


def get_first_line(s):
    first_line = s.split("\n")[0]
    tokens = first_line.split()
    if len(tokens) > 8:
        return " ".join(tokens[:8]) + "..."
    else:
        return first_line


async def get_element_description(element, tag_name, role_value, type_value):
    """
    Asynchronously generates a descriptive text for a web element based on its tag type.
    Handles various HTML elements like 'select', 'input', and 'textarea', extracting attributes and content relevant to accessibility and interaction.
    """

    salient_attributes = [
        "alt",
        "aria-describedby",
        "aria-label",
        "aria-role",
        "input-checked",
        "input-value",
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
    parent_locator = element.locator("xpath=..")
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
            options = await element.evaluate(
                "select => Array.from(select.options).map(option => option.text)",
                timeout=0,
            )
            text4 = " | ".join(options)

            if not text4:
                text4 = await element.text_content(timeout=0)
                if not text4:
                    text4 = await element.inner_text(timeout=0)

            return (
                parent_value + text1 + remove_extra_eol(text2.strip()) + text3 + text4
            )

    input_value = ""

    none_input_type = ["submit", "reset", "checkbox", "radio", "button", "file"]

    if tag_name == "input" or tag_name == "textarea":
        if role_value not in none_input_type and type_value not in none_input_type:
            text1 = "input value="
            text2 = await element.input_value(timeout=0)
            if text2:
                input_value = text1 + '"' + text2 + '"' + " "

    text_content = await element.text_content(timeout=0)
    text = (text_content or "").strip()
    if text:
        text = remove_extra_eol(text)
        if len(text) > 80:
            text_content_in = await element.inner_text(timeout=0)
            text_in = (text_content_in or "").strip()
            if text_in:
                return input_value + remove_extra_eol(text_in)
        else:
            return input_value + text

    # get salient_attributes
    text1 = ""
    for attr in salient_attributes:
        attribute_value = await element.get_attribute(attr, timeout=0)
        if attribute_value:
            text1 += f"{attr}=" + '"' + attribute_value.strip() + '"' + " "

    text = (parent_value + text1).strip()
    if text:
        return input_value + remove_extra_eol(text.strip())

    # try to get from the first child node
    first_child_locator = element.locator("xpath=./child::*[1]")

    num_childs = await first_child_locator.count()
    if num_childs > 0:
        for attr in salient_attributes:
            attribute_value = await first_child_locator.get_attribute(attr, timeout=0)
            if attribute_value:
                text1 += f"{attr}=" + '"' + attribute_value.strip() + '"' + " "

        text = (parent_value + text1).strip()
        if text:
            return input_value + remove_extra_eol(text.strip())

    return None


async def get_element_data(element, tag_name):
    tag_name_list = ["a", "button", "input", "select", "textarea", "adc-tab"]

    # await aprint(element,tag_name)
    if await element.is_hidden(timeout=0) or await element.is_disabled(timeout=0):
        return None

    tag_head = ""
    real_tag_name = ""
    if tag_name in tag_name_list:
        tag_head = tag_name
        real_tag_name = tag_name
    else:
        real_tag_name = await element.evaluate(
            "element => element.tagName.toLowerCase()", timeout=0
        )
        if real_tag_name in tag_name_list:
            # already detected
            return None
        else:
            tag_head = real_tag_name

    role_value = await element.get_attribute("role", timeout=0)
    type_value = await element.get_attribute("type", timeout=0)
    # await aprint("start to get element description",element,tag_name )
    description = await get_element_description(
        element, real_tag_name, role_value, type_value
    )
    if not description:
        return None

    rect = await element.bounding_box() or {"x": 0, "y": 0, "width": 0, "height": 0}

    if role_value:
        tag_head += " role=" + '"' + role_value + '"'
    if type_value:
        tag_head += " type=" + '"' + type_value + '"'

    box_model = [
        rect["x"],
        rect["y"],
        rect["x"] + rect["width"],
        rect["y"] + rect["height"],
    ]
    center_point = (
        (box_model[0] + box_model[2]) / 2,
        (box_model[1] + box_model[3]) / 2,
    )
    selector = element

    return [center_point, description, tag_head, box_model, selector, real_tag_name]


async def get_elements_with_playwright(page, type="default"):
    if type == "input":
        interactive_elements_selectors = [
            "button",
            "input",
            "textarea",
            '[role="button"]',
            '[role="combobox"]',
            '[role="textbox"]',
            '[type="button"]',
            '[type="combobox"]',
            '[type="textbox"]',
        ]
    else:
        interactive_elements_selectors = [
            "a",
            "button",
            "input",
            "select",
            "textarea",
            "adc-tab",
            '[role="button"]',
            '[role="radio"]',
            '[role="option"]',
            '[role="combobox"]',
            '[role="textbox"]',
            '[role="listbox"]',
            '[role="menu"]',
            '[type="button"]',
            '[type="radio"]',
            '[type="combobox"]',
            '[type="textbox"]',
            '[type="listbox"]',
            '[type="menu"]',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable]:not([contenteditable="false"])',
            "[onclick]",
            "[onfocus]",
            "[onkeydown]",
            "[onkeypress]",
            "[onkeyup]",
            "[checkbox]",
            '[aria-disabled="false"],[data-link]',
        ]

    tasks = []

    seen_elements = set()
    for selector in interactive_elements_selectors:
        locator = page.locator(selector)
        element_count = await locator.count()
        for index in range(element_count):
            element = locator.nth(index)
            tag_name = selector.replace(':not([tabindex="-1"])', "")
            tag_name = tag_name.replace(':not([contenteditable="false"])', "")
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


async def get_multi_inputs(page, type="default"):
    elements = await get_elements_with_playwright(page, type)

    all_candidate_ids = range(len(elements))
    ranked_elements = elements

    all_candidate_ids_with_location = []
    for element_id, element_detail in zip(all_candidate_ids, ranked_elements):
        all_candidate_ids_with_location.append(
            (element_id, round(element_detail[0][1]), round(element_detail[0][0]))
        )

    all_candidate_ids_with_location.sort(key=lambda x: (x[1], x[2]))

    all_candidate_ids = [
        element_id[0] for element_id in all_candidate_ids_with_location
    ]

    choices = format_choices(elements, all_candidate_ids)

    choice_text = format_options(choices)

    return elements, choices, choice_text
