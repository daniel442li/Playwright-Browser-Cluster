from openai import OpenAI

client = OpenAI()
import json

from dotenv import load_dotenv, find_dotenv
import json

load_dotenv(find_dotenv())


main_schema_reasoning = {
    "type": "object",
    "properties": {
        "answer": {
            "type": "string",
            "description": "The answer to the multiple choice QA. Should be in format 'A', 'B', 'AC', etc'"
        },
        "reasoning": {
            "type": "string",
            "description": "Why you choose the answer you did."
        },
    },
    "required": ["answer", "reasoning"],
}

main_schema = {
    "type": "object",
    "properties": {
        "answer": {
            "type": "string",
            "description": "The answer to the multiple choice QA. Should be in format 'A', 'B', 'AC', etc'"
        }
    },
    "required": ["answer"],
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
                            "description": "The answer to the multiple choice QA. Should be in format 'A', 'B', 'AC', etc"
                        },
                    },
                    "required": ["answer"]
                    },
        }
    },
    "required": ["answer"],
}


async def answer_multiple_choice(problem, quiz):
    print(quiz)
    completion = client.chat.completions.create(model="gpt-4-1106-preview",
    messages=[
        {"role": "system", "content": "You are an expert web navigator that imitates a human"},
        {"role": "user", "content": "You are imitating humans doing web navigation for a task. You will be passed a multiple choice QA of options to select and an instruction from the user. Identify the correct element based on its attributes and purpose, regardless of syntax correctness. Choose the correct answer for  " + "\n" + str(problem) + "\n" + "###" + "Multiple Choice QA: \n" + str(quiz)},
    ],
    functions=[{"name": "answer_multiple_choice", "parameters": main_schema_reasoning}],
    function_call={"name": "answer_multiple_choice"},
    temperature=0)

    main_json = (completion.choices[0].message.function_call.arguments)
    main_json = json.loads(main_json)

    print(main_json['answer'])

    return main_json['answer']


def answer_multiple_choice_forms(problem, quiz):
    print(quiz)
    completion = client.chat.completions.create(model="gpt-4-1106-preview",
    messages=[
        {"role": "system", "content": "You are an expert web navigator that imitates a human"},
        {"role": "user", "content": "You are imitating humans doing web navigation for a task. You will be passed a multiple choice QA of options to select and an instruction from the user. Identify the correct elements of inputs that coorespond to a form based on its attributes and purpose, regardless of syntax correctness. Choose the correct answer for  " + "\n" + str(problem) + "\n" + "###" + "Multiple Choice QA: \n" + str(quiz)},
    ],
    functions=[{"name": "answer_multiple_choice", "parameters": answer_all}],
    function_call={"name": "answer_multiple_choice"},
    temperature=0)

    main_json = (completion.choices[0].message.function_call.arguments)
    main_json = json.loads(main_json)

    print(main_json)

    return main_json['answer']

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