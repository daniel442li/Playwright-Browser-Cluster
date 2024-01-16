import json
import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored

GPT_MODEL = "gpt-3.5-turbo-0613"

import os
from dotenv import load_dotenv, find_dotenv
import json

load_dotenv(find_dotenv())


@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + os.getenv("OPENAI_API_KEY"),
    }
    json_data = {"model": model, "messages": messages}
    if tools is not None:
        json_data.update({"tools": tools})
    if tool_choice is not None:
        json_data.update({"tool_choice": tool_choice})
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e


def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "tool": "magenta",
    }
    
    for message in messages:
        if message["role"] == "system":
            print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "user":
            print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and message.get("function_call"):
            print(colored(f"assistant: {message['function_call']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and not message.get("function_call"):
            print(colored(f"assistant: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "tool":
            print(colored(f"function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))



tools = [
    {
        "type": "function",
        "function": {
            "name": "type",
            "description": "Types/searches into the page",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The item that they want to type into the page",
                    },
                   
                },
                "required": ["type"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "navigate_to",
            "description": "Given a user command, navigate to a web page URL. ",
            "parameters": {
                "type": "object",
                "properties": {
                    "link": {
                        "type": "string",
                        "description": "Return the working URL of the website according to your knowledge. Include .com, .net, etc. Don't include https://",
                    }
                },
                "required": ["link"]
            },
        }
    },
]


def convert_command(function_name, argument_string):
    if function_name == "get_current_weather":
        return f"get_current_weather(location='{argument_string['location']}', format='{argument_string['format']}')"
    elif function_name == "navigate_to":
        return {"command": "navigate", "parameters": {"link": f"https://{argument_string['link']}"}} 
 




def ai_command(command): 
    messages = []
    messages.append({"role": "user", "content": command})
    chat_response = chat_completion_request(
        messages, tools=tools
    )
    assistant_message = chat_response.json()["choices"][0]["message"]
    messages.append(assistant_message)
    function_name = (assistant_message['tool_calls'][0]['function']['name'])
    argument_string = json.loads(assistant_message['tool_calls'][0]['function']['arguments'])
    converted_command = convert_command(function_name, argument_string)
    return converted_command


#print(ai_command("go to new york times"))