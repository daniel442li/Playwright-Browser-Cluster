from config import OPENAI_API_KEY
from openai import OpenAI
import json

client = OpenAI(api_key=OPENAI_API_KEY)
model = "gpt-4-1106-preview"

main_schema = {
    "type": "object",
    "properties": {
        "industry": {
            "type": "string",
            "description": "The industry that the user works in.",
        },
        "position": {
            "type": "string",
            "description": "The position that the user has. Ex: Software Engineer, CEO, etc.",
        },
        "position_one": {
            "type": "string",
            "description": "The position that the user has in one word plural. Ex: Software Engineers, CEOs, etc.",
        },
    },
    "required": ["industry", "position", "position_one"],
}

name_schema = {
    "type": "object",
    "properties": {
        "first_name": {
            "type": "string",
            "description": "First name of the person.",
        },
    },
    "required": ["first_name"],
}

software_schema = {
    "type": "object",
    "properties": {
        "software": {
            "type": "string",
            "description": "Software example",
        },
        "explanation": {
            "type": "string",
            "description": "Brief explanation of how the answer was created. One sentence",
        },
    },
    "required": ["software", "explanation"],
}


def software_answer(industry):
    print(industry)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": f"You are an employee who works in {industry}",
            },
            {
                "role": "user",
                "content": (
                    f"Given {industry}, return softwares that someone in this industry would use. Name 2 and put and in between them."
                    "Example: Chiropractors use Practice Management Software, Electronic Health Records, and CRMs"
                ),
            },
        ],
        functions=[{"name": "answer_multiple_choice", "parameters": software_schema}],
        function_call={"name": "answer_multiple_choice"},
        temperature=0.1,
    )

    main_json = completion.choices[0].message.function_call.arguments
    main_json = json.loads(main_json)

    print(main_json)

    return main_json


name_schema = {
    "type": "object",
    "properties": {
        "first_name": {
            "type": "string",
            "description": "First name of the person.",
        },
    },
    "required": ["first_name"],
}


def name_information(user_info):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You will be passed in some information from the user and must extract the user's information",
            },
            {
                "role": "user",
                "content": (
                    "You will be passed in some information from the user and must extract the user's information"
                    "Please tell me some information about the user as accurately as possible."
                )
                + "\n"
                + "###"
                + "User Information: \n"
                + str(user_info),
            },
        ],
        functions=[{"name": "answer_multiple_choice", "parameters": name_schema}],
        function_call={"name": "answer_multiple_choice"},
        temperature=0,
    )

    main_json = completion.choices[0].message.function_call.arguments
    main_json = json.loads(main_json)

    print(main_json)

    return main_json


def user_information(user_info, schema):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You will be passed in some information from the user and must extract the user's information",
            },
            {
                "role": "user",
                "content": (
                    "You will be passed in some information from the user and must extract the user's information"
                    "Please tell me some information about the user as accurately as possible."
                )
                + "\n"
                + "###"
                + "User Information: \n"
                + str(user_info),
            },
        ],
        functions=[{"name": "answer_multiple_choice", "parameters": schema}],
        function_call={"name": "answer_multiple_choice"},
        temperature=0,
    )

    main_json = completion.choices[0].message.function_call.arguments
    main_json = json.loads(main_json)

    print(main_json)

    return main_json
