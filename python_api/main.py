from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from dotenv import load_dotenv, find_dotenv
import uuid

import logging
import subprocess
import threading
import queue
import time
import asyncio
from heartbeat import check_sessions
from gpt_commands import ai_command
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


class CreateSessionResponse(BaseModel):
    session_id: str

class CommandRequest(BaseModel):
    session_id: str
    command: str

class CommandResponse(BaseModel):
    status: str

class SessionList(BaseModel):
    sessions: list

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
sessions = {}



@app.post('/terminate_session/{session_id}', response_model=TerminateSessionResponse)
async def terminate_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]

    # Terminate the subprocess
    if session["process"].poll() is None:  # Check if process is still running
        session["process"].terminate()
        try:
            session["process"].wait(timeout=5)  # Wait for the process to terminate
        except subprocess.TimeoutExpired:
            session["process"].kill()  # Force kill if not terminated within timeout

    # Join the output thread to ensure it's finished
    if session["output_thread"].is_alive():
        session["output_thread"].join()

    # Remove the session from the dictionary
    del sessions[session_id]

    return {"message": "Session terminated successfully"}


def initialize_browser_session(session_id):
    python_path = "/Users/daniel-li/Code/browser-backend/venv/bin/python"
    # process = subprocess.Popen([python_path, '-u', '-i'],
    #                            stdin=subprocess.PIPE,
    #                            stdout=subprocess.PIPE,
    #                            stderr=subprocess.PIPE,
    #                            text=True)
    
    process = subprocess.Popen([python_path, '-u', '-i', '-m', 'asyncio'],
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           text=True)

    output_queue = queue.Queue()
    output_done = threading.Event()

    def read_output(out, q, done_event):
        for line in iter(out.readline, ''):
            q.put(line)
        out.close()
        done_event.set()

    output_thread = threading.Thread(target=read_output, args=(process.stdout, output_queue, output_done))
    output_thread.daemon = True
    output_thread.start()

    cookies = [{
        'name': 'li_at',
        'value': 'AQEDAStP9dYDmAa8AAABjQQs-DsAAAGNKDl8O04AtTnN10CX0bDxvPgQPWSD2YF7CIFVBbe5VfggjPe8z6rH7xcAHpi_XPSwLFhWa4BQlMy86Hw6Rlt0Dce5mc11WWGMZJpoIj_xcwTR7kFQJYYP_yI3',
        'domain': 'www.linkedin.com',
        'path': '/',
        # You can add other properties like 'expires', 'httpOnly', etc.
    }]

    initial_commands = [
    "from playwright.async_api import async_playwright",
    "playwright = await async_playwright().start()",
    "browser = await playwright.chromium.launch(headless=False)",
    "context = await browser.new_context()",
    "page = await context.new_page()",
    "await page.goto('https://playwright.dev/')",
    "await context.add_cookies(" + str(cookies) + ")"
    ]

    for command in initial_commands:
        process.stdin.write(command + "\n")
        process.stdin.flush()
        time.sleep(1)  # Give some time for command to execute

    # Store session data
    sessions[session_id] = {
        "process": process,
        "output_thread": output_thread,
        "output_queue": output_queue,
        "output_done": output_done
    }


@app.post('/create_session', response_model=CreateSessionResponse)
async def create_session():
    # session_id = str(uuid.uuid4())
    session_id = "test"
    initialize_browser_session(session_id)
    return {"session_id": session_id}


@app.post('/send_command', response_model=CommandResponse)
async def send_command(command_request: CommandRequest):
    session_id = command_request.session_id
    command_text = command_request.command

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session ID")

    session = sessions[session_id]
    process = session["process"]
    output_queue = session["output_queue"]
    output_done = session["output_done"]

    # Clear existing output
    while not output_queue.empty():
        output_queue.get()

    # Send command to subprocess
    print(command_text)
    processed_command = ai_command(command_text)
    process.stdin.write(processed_command + "\n")
    process.stdin.flush()

    # Wait for output with a timeout
    output = []
    timeout = 1.0  # Adjust timeout as needed
    start_time = time.time()
    while time.time() - start_time < timeout:
        while not output_queue.empty():
            output.append(output_queue.get())
        if output_done.is_set():
            break
        await asyncio.sleep(0.1)  # Non-blocking sleep

    return {"status": "Command executed", "output": output}


@app.get('/get_sessions', response_model=SessionList)
async def get_sessions():
    return {"sessions": list(sessions.keys())}



@app.get("/")
def read_root():
    return {"Welcome to our API :-)"}


#uvicorn main:app --reload