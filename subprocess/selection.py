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


def answer_multiple_choice(problem, quiz):
    completion = client.chat.completions.create(model="gpt-4-0613",
    messages=[
        {"role": "system", "content": "You are an expert web navigator that imitates a human"},
        {"role": "user", "content": "You are imitating humans doing web navigation for a task. You will be passed a multiple choice QA of options to select and an instruction from the user. Identify the correct element based on its attributes and purpose, regardless of syntax correctness. Choose the correct answer for  " + "\n" + str(problem) + "\n" + "###" + "Multiple Choice QA: \n" + str(quiz)},
    ],
    functions=[{"name": "answer_multiple_choice", "parameters": main_schema}],
    function_call={"name": "answer_multiple_choice"},
    temperature=0)

    main_json = (completion.choices[0].message.function_call.arguments)
    main_json = json.loads(main_json)

    print(main_json)

    return main_json['answer']


problem = "Start"

quiz = '''
If none of these elements match your target element, please select R. None of the other options match the correct element.
A. <a id="0">RPA Challenge</a>
B. <a id="1">Input Forms</a>
C. <a id="2">Shortest Path</a>
D. <a id="3">Movie Search</a>
E. <a id="4">Invoice Extraction</a>
F. <a id="5">RPA Stock Market</a>
G. <a id="6">EN</a>
H. <input id="9">parent_node: Company Name name="tmFKR"</input>
I. <input id="10">parent_node: Address name="cz4Vb"</input>
J. <input id="11">parent_node: Phone Number name="Tzy0D"</input>
K. <input id="12">parent_node: Role in Company name="5aRhx"</input>
L. <input id="13">parent_node: Last Name name="CPArI"</input>
M. <input id="14">parent_node: First Name name="3RHwa"</input>
N. <input id="15">parent_node: Email name="A1PTc"</input>
O. <input type="submit" id="16">parent_node: Company Name value="Submit"</input>
P. <a id="7">Download Excel cloud_download</a>
Q. <button id="8">Start</button>
R. None of the other options match the correct element
'''


print(answer_multiple_choice(problem, quiz))