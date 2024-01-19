from openai import OpenAI

client = OpenAI()
import json

from dotenv import load_dotenv, find_dotenv
import json

load_dotenv(find_dotenv())


main_schema = {
    "type": "object",
    "properties": {
        "identifier": {
            "type": "string",
            "description": "The answer to the question. Should be in format 'A', 'B', 'AC', etc'"
        },
    }
}



def convert(problem, quiz):
    completion = client.chat.completions.create(model="gpt-4-0613",
    messages=[
        {"role": "system", "content": "You are imitating humans doing web navigation for a task. You will be passed a quiz of options to select and an instruction from the user and you will choose the answer that you think is correct to navigate"},
        {"role": "user", "content": "Choose the correct answer for  " + "\n" + str(problem) + "\n" + "###" + "Multiple Choice QA: \n" + str(quiz)},
    ],
    functions=[{"name": "generate_schema", "parameters": main_schema}],
    function_call={"name": "generate_schema"},
    temperature=0)

    main_json = (completion.choices[0].message.function_call.arguments)
    main_json = json.loads(main_json)
    print(main_json)


problem = "Download excel button"

quiz = '''
A. <a id="0">RPA Challenge</a>
B. <a id="1">Input Forms</a>
C. <a id="2">Shortest Path</a>
D. <a id="3">Movie Search</a>
E. <a id="4">Invoice Extraction</a>
F. <a id="5">RPA Stock Market</a>
G. <a id="6">EN</a>
H. <input id="9">parent_node: Role in Company name="b7euI"</input>
I. <input id="10">parent_node: Company Name name="iXc73"</input>
J. <input id="11">parent_node: Phone Number name="996G2"</input>
K. <input id="12">parent_node: First Name name="K5SYU"</input>
L. <input id="13">parent_node: Address name="1ajYS"</input>
M. <input id="14">parent_node: Email name="vgLBP"</input>
N. <input id="15">parent_node: Last Name name="QYmIR"</input>
O. <input type="submit" id="16">parent_node: Role in Company value="Submit"</input>
P. <a id="7">Download Excel cloud_download</a>
Q. <button id="8">Round 1</button>


'''


convert(problem, quiz)