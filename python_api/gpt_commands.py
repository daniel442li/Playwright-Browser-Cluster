import json
import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored

GPT_MODEL = "gpt-4-1106-preview"

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
        "description": "Call when you see keywords such as SEARCH, LOOK UP, FIND, TYPE",
        "function": {
            "name": "search",
            "description": "Call thsi when a user wants to utilize a search / input on the webpage. KEYWORDS: SEARCH, LOOK UP, FIND",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query that the user wants to search up in the search bar",
                    },
                },
                "required": ["query"],
            },
        }
    },
    {
        "type": "function",
        "description": "Call when you see keywords such as GO TO, NAVIGATE TO, VISIT, OPEN",
        "function": {
            "name": "navigate_to",
            "description": "Given a user command, navigate to a web page URL. Include .com, .net, etc. Don't include https://. KEYWORDS: GO TO, NAVIGATE TO, VISIT, OPEN",
            "parameters": {
                "type": "object",
                "properties": {
                    "link": {
                        "type": "string",
                        "description": "The url of the website to navigate to",
                    }
                },
                "required": ["link"]
            },
        }
    },
    {
        "type": "function",
        "description": "Call when you see keywords such as CLICK, SELECT, CHOOSE, PICK",
        "function": {
            "name": "click",
            "description": "Call this when the user wants to click/select an element. KEYWORDS: CLICK, SELECT, CHOOSE, PICK",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "The description of the element to click. The more specific the better.",
                    },
                },
                "required": ["selector"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press",
            "description": "Call when you see keywords such as PRESS, HIT, ENTER, TAB, SPACE, ARROW KEYS",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "The button on the keyboard that the user wants to press",
                        "enum": ["Enter", "Tab", "Space", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"],
                    },
                },
                "required": ["key"],
            },
        }
    }
]



def convert_command(function_name, argument_string):
    if function_name == "search":
        return {"command": "search", "parameters": {"query": argument_string['query']}} 
    elif function_name == "navigate_to":
        return {"command": "navigate", "parameters": {"link": f"https://{argument_string['link']}"}} 
    elif function_name == "click":
        return {"command": "click", "parameters": {"selector": argument_string['selector']}}
    elif function_name == 'press':
        return {"command": "press", "parameters": {"key": argument_string['key']}}
 




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


