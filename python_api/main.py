from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from dotenv import load_dotenv, find_dotenv
from typing import Dict
import logging
import asyncio
from heartbeat import check_sessions
from browser import BrowserAutomation
import json
import base64

load_dotenv(find_dotenv())

logging.basicConfig(level=logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Before API starts
    asyncio.create_task(check_sessions(sessions))
    yield
    # After exiting the context manager, do some cleanup


app = FastAPI(lifespan=lifespan)

# Step 2: Setup the logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CreateSessionRequest(BaseModel):
    session_id: str


class CreateSessionResponse(BaseModel):
    session_id: str


class CommandRequestNavigate(BaseModel):
    session_id: str
    link: str

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
binary_image_data: Dict[str, bytes] = {}

class ImageData(BaseModel):
    image_data: str

@app.post("/receive_image/{session_id}")
async def receive_image(session_id: str, image_data: ImageData):
    try:
        content = base64.b64decode(image_data.image_data)
        binary_image_data[session_id] = content
        return {"message": "Image received"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image data")


@app.get("/stream_image/{session_id}")
async def stream_image(session_id: str):
    if session_id not in binary_image_data:
        raise HTTPException(status_code=404, detail="Session not found")

    image_data = binary_image_data[session_id]
    base64_encoded_data = base64.b64encode(image_data).decode('utf-8')

    # Function to generate the data to be streamed
    def file_generator():
        yield f"data: {base64_encoded_data}\n\n"
        # Remove the image data from dictionary after sending it
        #del binary_image_data[session_id]

    return StreamingResponse(file_generator(), media_type="text/event-stream")


@app.post("/terminate_session", response_model=TerminateSessionResponse)
async def terminate_session(terminate_session_request: TerminateSessionRequest):
    session_id = terminate_session_request.session_id
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    browser = sessions[session_id]

    await browser.close()

    del sessions[session_id]
    del binary_image_data[session_id]

    return {"message": "Session terminated successfully"}


def initialize_browser_session(session_id):
    # Instantiate the BrowserAutomation object
    automation = BrowserAutomation(session_id)

    # Run the startup script in a separate asyncio task
    asyncio.create_task(automation.start())

    # cookies = [{
    #     'name': 'li_at',
    #     'value': 'AQEDAStP9dYDmAa8AAABjQQs-DsAAAGNKDl8O04AtTnN10CX0bDxvPgQPWSD2YF7CIFVBbe5VfggjPe8z6rH7xcAHpi_XPSwLFhWa4BQlMy86Hw6Rlt0Dce5mc11WWGMZJpoIj_xcwTR7kFQJYYP_yI3',
    #     'domain': 'www.linkedin.com',
    #     'path': '/',
    #     # You can add other properties like 'expires', 'httpOnly', etc.
    # }]

    # initial_commands = [
    # "await context.add_cookies(" + str(cookies) + ")"
    # ]

    return automation


@app.post("/create_session", response_model=CreateSessionResponse)
async def create_session(create_session_request: CreateSessionRequest):
    session_id = create_session_request.session_id

    if session_id in sessions:
        raise HTTPException(status_code=409, detail="Session ID already exists")
    browser = initialize_browser_session(session_id)
    sessions[session_id] = browser
    return {"session_id": session_id}


@app.post("/send_command_navigate", response_model=CommandResponse)
async def send_command_navigate(command_request_navigate: CommandRequestNavigate):
    session_id = command_request_navigate.session_id
    link = command_request_navigate.link

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session ID")

    browser = sessions[session_id]

    try:
        future = await browser.navigate(link)

        result = await future

        result = json.loads(result)

        action = result.get("command")
        parameters = result.get("parameters", [])

        await asyncio.sleep(0.5)
        await browser.send_screenshot()

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

        await asyncio.sleep(0.5)
        await browser.send_screenshot()

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

        await asyncio.sleep(0.5)
        await browser.send_screenshot()

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

        await asyncio.sleep(0.5)
        await browser.send_screenshot()

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
        await asyncio.sleep(0.5)
        await browser.send_screenshot()

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

        await asyncio.sleep(0.5)
        await browser.send_screenshot()

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
        await asyncio.sleep(0.5)
        await browser.send_screenshot()

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
    


@app.get("/")
def read_root():
    return {"Welcome to our API :-)"}


# uvicorn main:app --reload
