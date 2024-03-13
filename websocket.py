from fastapi import WebSocket
import json
from shared import sessions

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await receive_and_parse(websocket)
            if validate_data(data):
                await handle_action(websocket, data)
            else:
                await websocket.send_text("Error: Invalid or missing session_id.")
    except Exception as e:
        print(f"WebSocket disconnected: {e}")

async def receive_and_parse(websocket):
    text_data = await websocket.receive_text()
    return json.loads(text_data)

def validate_data(data):
    return "id" in data and data["id"] in sessions

async def handle_action(websocket, data):
    session_id = data["id"]
    session = sessions[session_id]
    action = data.get("action")

    action_handlers = {
        'click': handle_click,
        'hover': handle_hover,
        'go_back': handle_go_back,
        'go_forward': handle_go_forward,
        'press': handle_press,
        'scroll': handle_scroll,
        'insert_bounding': handle_insert_bounding,
    }

    if action in action_handlers:
        await action_handlers[action](websocket, session, data)
    else:
        await websocket.send_text("Error: Invalid action.")


async def handle_click(websocket, session, data):
    coordinates = data.get("coordinates")
    if coordinates and "x" in coordinates and "y" in coordinates:
        click_result = await session.coord_click(coordinates["x"], coordinates["y"])
        await websocket.send_text(f"Click action performed: {click_result}")
    else:
        await websocket.send_text("Error: Missing/invalid coordinates for click action.")


async def handle_hover(websocket, session, data):
    coordinates = data.get("coordinates")
    if coordinates and "x" in coordinates and "y" in coordinates:
        await session.hover_at_coordinates(coordinates["x"], coordinates["y"])
        await websocket.send_text(f"Hover action performed at: {coordinates['x']}, {coordinates['y']}")
    else:
        await websocket.send_text("Error: Missing/invalid coordinates for hover action.")


async def handle_go_back(websocket, session, data):
    await session.go_back()
    await websocket.send_text("Browser navigated back successfully.")


async def handle_go_forward(websocket, session, data):
    await session.go_forward()
    await websocket.send_text("Browser navigated forward successfully.")


async def handle_press(websocket, session, data):
    if "key" in data:
        await session.press_keys(data["key"])
        await websocket.send_text(f"Key {data['key']} pressed successfully.")
    else:
        await websocket.send_text("Error: Missing key for press action.")


async def handle_scroll(websocket, session, data):
    if "amount" in data:
        await session.scroll(data["amount"])
        await websocket.send_text(f"Scrolled by {data['amount']} successfully.")
    else:
        await websocket.send_text("Error: Missing amount for scroll action.")


async def handle_insert_bounding(websocket, session, data):
    if "query" in data:
        result = await session.get_accessibility_tree(data["query"])
        await websocket.send_text(f"Accessibility tree retrieved for query {data['query']}: {result}")
    else:
        await websocket.send_text("Error: Missing query for insert bounding action.")
