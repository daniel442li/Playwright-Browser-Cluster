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
from gpt_commands import ai_command
from browser import BrowserAutomation
load_dotenv(find_dotenv())


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Before API starts
    asyncio.create_task(check_sessions(sessions))
    yield
    # After exiting the context manager, do some cleanup


app = FastAPI(lifespan=lifespan)

# Step 2: Setup the logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CreateSessionRequest(BaseModel):
    session_id: str

class CreateSessionResponse(BaseModel):
    session_id: str

class CommandRequest(BaseModel):
    session_id: str
    command: str

class CommandResponse(BaseModel):
    status: str

class SessionList(BaseModel):
    sessions: list

class TerminateSessionRequest(BaseModel):
    session_id: str

class TerminateSessionResponse(BaseModel):
    message: str

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
screenshots: Dict[str, asyncio.Queue] = {}



@app.post("/receive_screenshot/{session_id}")
async def receive_screenshot(session_id: str, file: UploadFile = File(...)):
    if session_id not in sessions:
        screenshots[session_id] = asyncio.Queue()
    await screenshots[session_id].put(await file.read())
    return {"message": "Screenshot received"}


@app.get("/stream_screenshot/{session_id}")
async def stream_screenshot(session_id: str):
    if session_id not in screenshots:
        raise HTTPException(status_code=404, detail="Session not found")

    async def generate_screenshots(session_id):
        while True:
            if not screenshots[session_id].empty():
                screenshot = await screenshots[session_id].get()
                yield screenshot
            await asyncio.sleep(1)  # Adjust the sleep time as needed

    return StreamingResponse(generate_screenshots(session_id), media_type="image/png")


@app.post('/terminate_session', response_model=TerminateSessionResponse)
async def terminate_session(terminate_session_request: TerminateSessionRequest):
    session_id = terminate_session_request.session_id
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    browser = sessions[session_id]

    await browser.close()
    
    del sessions[session_id]
    del screenshots[session_id]

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



@app.post('/create_session', response_model=CreateSessionResponse)
async def create_session(create_session_request: CreateSessionRequest):
    session_id = create_session_request.session_id
    browser = initialize_browser_session(session_id)
    sessions[session_id] = browser
    screenshots[session_id] = asyncio.Queue()
    return {"session_id": session_id}


@app.post('/send_command', response_model=CommandResponse)
async def send_command(command_request: CommandRequest):
    session_id = command_request.session_id
    command_text = command_request.command

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session ID")

    browser = sessions[session_id]

    command = ai_command(command_text)

    await browser.add_command_async(command)
    
    return {"status": "Command executed"}


@app.get('/get_sessions', response_model=SessionList)
async def get_sessions():
    return {"sessions": list(sessions.keys())}



@app.get("/")
def read_root():
    return {"Welcome to our API :-)"}


#uvicorn main:app --reload