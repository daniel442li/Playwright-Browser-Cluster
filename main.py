from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional
from dotenv import load_dotenv, find_dotenv
from typing import Dict
import logging
import asyncio
from browser import BrowserAutomation
import json

load_dotenv(find_dotenv())


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Before API starts
    yield
    # After exiting the context manager, do some cleanup


app = FastAPI(lifespan=lifespan)

# Step 2: Setup the logging configuration
logging.basicConfig(
    #level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CreateSessionRequest(BaseModel):
    session_id: str


class CreateSessionResponse(BaseModel):
    session_id: str


class CommandRequestNavigate(BaseModel):
    session_id: str
    link: str
    cookie: Optional[list] = None 

class CommandRequestSearch(BaseModel):
    session_id: str
    query: str

class CommandRequestClick(BaseModel):
    session_id: str
    query: str

class CommandRequestPress(BaseModel):
    session_id: str
    key: str


class CommandResponse(BaseModel):
    status: str
    action: str
    parameters: list

class FillForms(BaseModel):
    session_id: str

class CacheRequest(BaseModel):
    session_id: str
    parameters: list


class SessionList(BaseModel):
    sessions: list


class TerminateSessionRequest(BaseModel):
    session_id: str


class TerminateSessionResponse(BaseModel):
    message: str


class SessionExistsRequest(BaseModel):
    session_id: str


class SessionExistsResponse(BaseModel):
    exists: bool

class SessionReadyResponse(BaseModel):
    ready: bool


class DOMData(BaseModel):
    dom_data: str

# Allow CORS
origins = [
    "http://localhost:3000",  # React app
    "http://localhost:8080",  # Also allow localhost for local development
    "http://localhost:8000",  # Allow any localhost (for local development)
]

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dictionary to store session data
sessions: Dict[str, BrowserAutomation] = {}

@app.post("/terminate_session", response_model=TerminateSessionResponse)
async def terminate_session(terminate_session_request: TerminateSessionRequest):
    session_id = terminate_session_request.session_id
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    browser = sessions[session_id]

    await browser.close()

    del sessions[session_id]

    return {"message": "Session terminated successfully"}


async def initialize_browser_session(session_id):
    # Instantiate the BrowserAutomation object
    automation = BrowserAutomation(session_id)

    # Run the startup script in a separate asyncio task
    await automation.start()
    return automation


@app.post("/create_session", response_model=CreateSessionResponse)
async def create_session(create_session_request: CreateSessionRequest):
    session_id = create_session_request.session_id

    if session_id in sessions:
        browser = sessions[session_id]
        await browser.close()
    
    browser = await initialize_browser_session(session_id)
    sessions[session_id] = browser
    return {"session_id": session_id}


@app.post("/send_command_navigate", response_model=CommandResponse)
async def send_command_navigate(command_request_navigate: CommandRequestNavigate):
    session_id = command_request_navigate.session_id
    link = command_request_navigate.link
    cookie = command_request_navigate.cookie

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session ID")

    browser = sessions[session_id]

    if cookie is not None:
        for c in cookie:
            c['sameSite'] = 'None'
            await browser.add_cookie(c)

    try:
        future = await browser.navigate(link)

        result = await future

        result = json.loads(result)

        action = result.get("command")
        parameters = result.get("parameters", [])

        # Return the result in the response
        return {
            "status": "Command executed",
            "action": action,
            "parameters": parameters,
        }
    except Exception as e:
        # Handle exceptions (e.g., command failures, timeouts)
        return {"status": "Error", "message": str(e)}


@app.post("/send_command_press", response_model=CommandResponse)
async def send_command_press(command_request_press: CommandRequestPress):
    session_id = command_request_press.session_id
    key = command_request_press.key

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session ID")

    browser = sessions[session_id]

    try:
        future = await browser.press(key)

        result = await future

        result = json.loads(result)


        action = result.get("command")
        parameters = result.get("parameters", [])

        # Return the result in the response
        return {
            "status": "Command executed",
            "action": action,
            "parameters": parameters,
        }
    except Exception as e:
        # Handle exceptions (e.g., command failures, timeouts)
        return {"status": "Error", "message": str(e)}


@app.post("/send_command_search", response_model=CommandResponse)
async def send_command_search(command_request_search: CommandRequestSearch):
    session_id = command_request_search.session_id
    query = command_request_search.query

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session ID")

    browser = sessions[session_id]

    try:
        future = await browser.search(query)

        result = await future

        result = json.loads(result)


        action = result.get("command")
        parameters = result.get("parameters", [])

        # Return the result in the response
        return {
            "status": "Command executed",
            "action": action,
            "parameters": parameters,
        }
    except Exception as e:
        # Handle exceptions (e.g., command failures, timeouts)
        return {"status": "Error", "message": str(e)}
    

@app.post("/send_cached_search")
async def send_cached_search(command_cache_search: CacheRequest):
    session_id = command_cache_search.session_id
    parameters = command_cache_search.parameters

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session ID")

    browser = sessions[session_id]

    try:
        await browser.search_cache(
                parameters[0], parameters[1], parameters[2], parameters[3]
        )

        # Return the result in the response
        return {"status": "Cached command executed"}

    except Exception as e:
        # Handle exceptions (e.g., command failures, timeouts)
        return {"status": "Error", "message": str(e)}
    

@app.post("/send_command_click", response_model=CommandResponse)
async def send_command_click(command_request_search: CommandRequestClick):
    session_id = command_request_search.session_id
    query = command_request_search.query

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session ID")

    browser = sessions[session_id]        

    try:
        future = await browser.click(query)

        result = await future

        result = json.loads(result)


        action = result.get("command")
        parameters = result.get("parameters", [])


        # Return the result in the response
        return {
            "status": "Command executed",
            "action": action,
            "parameters": parameters,
        }
    except Exception as e:
        # Handle exceptions (e.g., command failures, timeouts)
        return {"status": "Error", "message": str(e)}


@app.post("/send_cached_click")
async def send_cached_click(command_cache_search: CacheRequest):
    session_id = command_cache_search.session_id
    parameters = command_cache_search.parameters

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session ID")

    browser = sessions[session_id]

    try:
        await browser.click_cache(parameters[0], parameters[1])
        # Return the result in the response
        return {"status": "Cached command executed"}

    except Exception as e:
        # Handle exceptions (e.g., command failures, timeouts)
        return {"status": "Error", "message": str(e)}
    

@app.post("/send_fill_forms")
async def send_fill_forms(fill_forms: FillForms):
    session_id = fill_forms.session_id

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session ID")

    browser = sessions[session_id]

    try:
        future = await browser.fill_out_form()

        result = await future

        result = json.loads(result)


        action = result.get("command")
        parameters = result.get("parameters", [])
        
        # Return the result in the response
        return {
            "status": "Command executed",
            "action": action,
            "parameters": parameters,
        }
    except Exception as e:
        # Handle exceptions (e.g., command failures, timeouts)
        return {"status": "Error", "message": str(e)}
    

@app.post("/send_cached_fill_forms")
async def send_cached_fill_forms(command_cache_search: CacheRequest):
    session_id = command_cache_search.session_id
    parameters = command_cache_search.parameters

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session ID")

    browser = sessions[session_id]

    try:
        await browser.fill_out_form_cache(parameters)
        # Return the result in the response
        return {"status": "Cached command executed"}

    except Exception as e:
        # Handle exceptions (e.g., command failures, timeouts)
        return {"status": "Error", "message": str(e)}


@app.get("/session_exists/{session_id}", response_model=SessionExistsResponse)
async def session_exists(session_id: str):
    return {"exists": session_id in sessions}


@app.get("/session_ready/{session_id}", response_model=SessionReadyResponse)
async def session_ready(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session ID")

    browser = sessions[session_id]


    return {"ready": browser.ready}


@app.post("/update_activity_time/{session_id}")
async def update_activity_time(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session ID not found")

    browser = sessions[session_id]
    browser.update_activity_time()
    return {"status": "Activity time updated"}


@app.post("/start_stream/{session_id}")
async def start_stream(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session ID not found")

    browser = sessions[session_id]
    try:
        await browser.start_stream()
        return {"status": "Stream started"}
    except Exception as e:
        return {"status": "Error", "message": str(e)}


class CoordClickBody(BaseModel):
    x: float
    y: float

@app.post("/coord_click/{session_id}")
async def coord_click(session_id: str, body: CoordClickBody):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session ID not found")

    browser = sessions[session_id]
    try:
        future = await browser.coord_click(body.x, body.y)
        result = await future
        return {"status": "Success", "message": result}
    except Exception as e:
        return {"status": "Error", "message": str(e)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Wait for any message from the client
            data = await websocket.receive_text()
            data = json.loads(data)
            print(f"Message received: {data}")

            if "id" in data:
                session_id = data["id"]
                if session_id in sessions:
                    session = sessions[session_id]
                    action = data.get("action")
                    coordinates = data.get("coordinates")
                    try:
                        if action == 'click' and coordinates and "x" in coordinates and "y" in coordinates:
                            click_result = await session.coord_click(coordinates["x"], coordinates["y"])
                            await websocket.send_text(f"Click action performed: {click_result}")
                        elif action == 'hover' and coordinates and "x" in coordinates and "y" in coordinates:
                            await session.hover_at_coordinates(coordinates["x"], coordinates["y"])
                            await websocket.send_text(f"Hover action performed at: {coordinates['x']}, {coordinates['y']}")
                        elif action == 'go_back':
                            await session.go_back()
                            await websocket.send_text("Browser navigated back successfully.")
                        elif action == 'go_forward':
                            await session.go_forward()
                            await websocket.send_text("Browser navigated forward successfully.")
                        elif action == 'press':
                            await session.press_keys(data["key"])
                        elif action == 'scroll':
                            await session.scroll(data["amount"])
                        else:
                            await websocket.send_text("Error: Invalid action or missing/invalid coordinates.")
                    except Exception as e:
                        await websocket.send_text(f"Error performing {action} action: {str(e)}")
                else:
                    await websocket.send_text("Error: Invalid or missing session_id.")
            # Echo the received message back to the client
            await websocket.send_text(f"Message text was: {data}")
    except Exception as e:
        # Handle exceptions (e.g., WebSocket disconnection)
        await websocket.close()
        print(f"WebSocket disconnected: {e}")


@app.get("/")
def read_root():
    return {"Welcome to our API :-)"}


# uvicorn main:app 

# uvicorn main:app --host 0.0.0.0 --port 8000
