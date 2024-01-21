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



system_message = """
You are a very helpful assistant. Your job is to choose the best posible action to solve the user question or task.

These are the available actions:
- search: Call when you see keywords such as SEARCH, LOOK UP, FIND
- navigate: Call when you see keywords such as GO TO, NAVIGATE TO, VISIT, OPEN
- click: Call when you see keywords such as CLICK, SELECT, CHOOSE, PICK
- press: Call this when the user wants to click/select an element. KEYWORDS: CLICK, SELECT, CHOOSE, PICK
- fill_out_form: Call when you see keywords such as FILL, COMPLETE, INPUT, TYPE in reference to form fields

"""

agent_function_thought = {
    'name': 'select_action',
    'description': 'Selects an action',
    'parameters': {
        'type': 'object',
        'properties': {
            'thought': {
                'type': 'string',
                'description': 'The reasoning behind the selection of an action'
            },
            'action': {
                'type': 'string',
                'enum': ["search", "navigate", "click", "press", "fill_out_form"],
                'description': 'Action name to accomplish a task'
            }
        },
        'required': ['thought', 'action']
    }
}

agent_function = {
    "type": "function",
    "function": {
        'name': 'select_action',
        'description': 'Selects an action',
        'parameters': {
            'type': 'object',
            'properties': {
                'action': {
                    'type': 'string',
                    'enum': ["search", "navigate", "click", "press", "fill_out_form"],
                    'description': 'Action name to accomplish a task'
                },
                
            },
            'required': ['action']
            
        }
    }
}



tools = [
    {
        "type": "function",
        "function": {
            "name": "search",
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
        "function": {
            "name": "navigate",
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
        "function": {
            "name": "click",
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
        "name": "fill_out_form",
        "parameters": {
            "type": "object",
            "properties": {
                "fields": {
                    "type": "array",
                    "description": "An array of objects representing form fields and the values to input. If no fields specified, return an empty array.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "form_description": {
                                "type": "string",
                                "description": "A description of what the input field is for"
                            },
                            "value": {
                                "type": "string",
                                "description": "The value to enter into the form field"
                            }
                        },
                        "required": ["selector", "value"]
                    }
                }
            },
            "required": ["fields"],
        }
    }
}
]


def convert_command(action, command):
    messages = []

    if action == 'fill_out_form':
        messages.append({"role": "system", "content": "Return an empty array if no forms specified"})

    messages.append({"role": "user", "content": command})
    chat_response = chat_completion_request(
        messages, tools=tools, tool_choice={"type": "function", "function": {"name": action}}
    )

    assistant_message = chat_response.json()["choices"][0]["message"]
    argument_string = json.loads(assistant_message['tool_calls'][0]['function']['arguments'])

    if action == "search":
        return {"command": "search", "parameters": {"query": argument_string['query']}} 
    elif action == "navigate":
        if (argument_string['link'].startswith("https://")):
            return {"command": "navigate", "parameters": {"link": argument_string['link']}}
        else:
            return {"command": "navigate", "parameters": {"link": f"https://{argument_string['link']}"}} 
    elif action == "click":
        return {"command": "click", "parameters": {"selector": argument_string['selector']}}
    elif action == 'press':
        return {"command": "press", "parameters": {"key": argument_string['key']}}
    elif action == 'fill_out_form':
        return {"command": "fill_out_form", "parameters": {"fields": argument_string['fields']}}
 




def ai_command(command): 
    messages = []
    messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": command})
    chat_response = chat_completion_request(
        messages, tools=[agent_function], tool_choice={"type": "function", "function": {"name": "select_action"}}
    )
    assistant_message = chat_response.json()

    assistant_message = chat_response.json()["choices"][0]["message"]
    messages.append(assistant_message)

    argument_string = json.loads(assistant_message['tool_calls'][0]['function']['arguments'])
    converted_command = convert_command(argument_string['action'], command)


    return converted_command

    
    #return converted_command

def test():
    import time
    start = time.time()
    print(ai_command("go to google"))
    print(time.time() - start)

    start = time.time()
    print(ai_command("go to google"))
    print(time.time() - start)

    start = time.time()
    print(ai_command("go to google"))
    print(time.time() - start)

    start = time.time()
    print(ai_command("go to google"))
    print(time.time() - start)

    start = time.time()
    print(ai_command("go to google"))
    print(time.time() - start)


test()