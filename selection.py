from openai import OpenAI
import json

from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)
model = "gpt-4-1106-preview"
image_model = ''

main_schema = {
    "type": "object",
    "properties": {
        "answer": {
            "type": "string",
            "description": "The answer to the multiple choice QA. Should be in format 'A', 'B', 'AC', etc'",
        }
    },
    "required": ["answer"],
}


main_schema_reasoning = {
    "type": "object",
    "properties": {
        "answer": {
            "type": "string",
            "description": "The answer to the multiple choice QA. Should be in format 'A', 'B', 'AC', etc'",
        },
        "reasoning": {
            "type": "string",
            "description": "The reasoning behind your answer",
        }
    },
    "required": ["answer", "reasoning"],
}



answer_all = {
    "type": "object",
    "properties": {
        "answer": {
            "type": "array",
            "description": "Answers to the multiple choice questions. Should be in format ['A', 'B', 'AC'], etc'",
            "items": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "The answer to the multiple choice QA. Should be in format 'A', 'B', 'AC', etc",
                    },
                    "label": {
                        "type": "string",
                        "description": "After picking your answer, pick a label based on the parent node / the text around the element. Should be like 'Company Name', 'Last Name', etc. Look at the text in the multiple choice they are ordered. Do not just call it Input Text. Find the right element in the DOM.",
                    },
                    "type": {
                        "type": "string",
                        "description": "The type of element. The three types are input (text, email, etc), file (file upload), and select (dropdown).",
                        "enum": ["input", "file", "select"],
                    }
                },
                "required": ["answer", "label", "type"],
            },
        }
    },
    "required": ["answer"],
}


async def answer_multiple_choice(problem, quiz):
    print(quiz)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are an expert web navigator that imitates a human. ",
            },
            {
                "role": "user",
                "content": (
                    "You are imitating humans doing web navigation for a task. "
                    "You will be passed a multiple choice QA of options to select and an instruction from the user. "
                    "The multiple choices are ordered row-wise from left to right. "
                    "After it hits the right border it goes from top to bottom. "
                    "Identify the correct element based on its attributes and purpose, regardless of syntax correctness. "
                    "Choose the correct answer for "
                ) + "\n"
                + str(problem)
                + "\n"
                + "###"
                + "Multiple Choice QA: \n"
                + str(quiz),
            },
        ],
        functions=[
            {"name": "answer_multiple_choice", "parameters": main_schema}
        ],
        function_call={"name": "answer_multiple_choice"},
        temperature=0,
    )
    

    main_json = completion.choices[0].message.function_call.arguments
    main_json = json.loads(main_json)

    print(main_json["answer"])

    return main_json["answer"]


async def answer_multiple_choice_forms(quiz):
    print(quiz)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are an expert form filler who fills forms in a web browser.",
            },
            {
                "role": "user",
                "content": (
                    "You are an expert form filler who fills forms in a web browser for job applications."
                    "You will be passed a multiple choice QA of HTML and an instruction from the user."
                    "You want to fill out all the forms on the website. You will find all form elements to fill regardless of syntax correctness."
                    "The multiple choices are ordered row-wise from left to right. "
                    "After it hits the right border it goes from top to bottom. "
                    "You will only select elements that are form elements. These include inputs, textareas, comboboxes, etc."
                    "Do not select submit buttons or other non-form elements."
                    #"You will only fill out the form elements which are required. This is indicated by the asterisk (*) symbol. If a form element is required, you must fill it out. If it is not required, you can skip it."
                    "Please also specify the type of element. The three types are input (text, email, etc), file (file upload), and select (dropdown)."
                    "You should seperate each answer choice into a seperate array element. The final answer should look something like this: ['A', 'F', 'K'], etc."
                    "After picking your answer, pick a label based on the parent node / the text around the element. Should be like 'Company Name', 'Last Name', etc. Look at the text in the multiple choice they are ordered. Do not just call it Input Text. Find the right element based on the DOM."
                ) + "\n"
                + "###"
                + "Multiple Choice QA: \n"
                + str(quiz),
            },
        ],
        functions=[{"name": "answer_multiple_choice", "parameters": answer_all}],
        function_call={"name": "answer_multiple_choice"},
        temperature=0,
    )

    main_json = completion.choices[0].message.function_call.arguments
    main_json = json.loads(main_json)

    print(main_json)

    return main_json["answer"]


# quiz = '''
# If none of these elements match your target element, please select J. None of the other options match the correct element.
# A. <input id="1">parent_node: Company Name name="pMHaI"</input>
# B. <input id="2">parent_node: Last Name name="qnqsL"</input>
# C. <input id="3">parent_node: Email name="zgJEL"</input>
# D. <input id="4">parent_node: Address name="MXvfE"</input>
# E. <input id="5">parent_node: Phone Number name="vl50G"</input>
# F. <input id="6">parent_node: First Name name="NxoG9"</input>
# G. <input id="7">parent_node: Role in Company name="nbPiz"</input>
# H. <input type="submit" id="8">parent_node: Company Name value="Submit"</input>
# I. <button id="0">Round 1</button>
# J. None of the other options match the correct element

# '''


# answer_multiple_choice_forms("All form elements", quiz)
