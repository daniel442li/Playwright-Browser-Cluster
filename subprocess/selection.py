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


def convert(problem, quiz):
    completion = client.chat.completions.create(model="gpt-4-0613",
    messages=[
        {"role": "system", "content": "You are imitating humans doing web navigation for a task. You will be passed a multiple choice QA of options to select and an instruction from the user. "},
        {"role": "user", "content": "Identify the correct element based on its attributes and purpose, regardless of syntax correctness. Choose the correct answer for  " + "\n" + str(problem) + "\n" + "###" + "Multiple Choice QA: \n" + str(quiz)},
    ],
    functions=[{"name": "generate_schema", "parameters": main_schema}],
    function_call={"name": "generate_schema"},
    temperature=0)

    main_json = (completion.choices[0].message.function_call.arguments)
    main_json = json.loads(main_json)
    print(main_json)

    # return main_json['identifier']


problem = "Search element"

quiz = '''
If none of these elements match your target element, please select B. None of the other options match the correct element.
A. <input type="text" id="0">aria-label="Search" name="search_query" placeholder="Search"</input>
B. None of the other options match the correct element


'''


convert(problem, quiz)