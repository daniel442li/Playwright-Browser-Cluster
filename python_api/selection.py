from openai import OpenAI

client = OpenAI()
import json

from dotenv import load_dotenv, find_dotenv
import json

load_dotenv(find_dotenv())


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


async def answer_multiple_choice(problem, quiz):
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

    return main_json['answer']