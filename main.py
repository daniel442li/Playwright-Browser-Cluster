from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi import WebSocket, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv, find_dotenv
from models import *
import logging
import asyncio
from browser import BrowserAutomation
import json
import os
import sys
import sentry_sdk
from interactive_browser.websocket import interactive_websocket_endpoint
from shared import sessions
from executor.run_executor import ExecutorWebsocket
from document_extractor.extractor import router as extractor_router
from playwright.async_api import async_playwright

# Import configurations from config.py
from config import (
    SENTRY_DSN,
    SENTRY_TRACES_SAMPLE_RATE,
    SENTRY_ENVIRONMENT,
    CORS_ORIGINS,
)

# Initialize Sentry with variables from config.py
sentry_sdk.init(
    dsn=SENTRY_DSN,
    traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
    environment=SENTRY_ENVIRONMENT,
)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv(find_dotenv())


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Before API starts
    yield
    # After exiting the context manager, do some cleanup


app = FastAPI(lifespan=lifespan)

logging.basicConfig(
    # level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0


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

    print(session_id)

    if session_id in sessions:

        print("Session already exists")
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
            c["sameSite"] = "None"
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
        return {"ready": False}

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


@app.get("/get_accessibility_tree/{session_id}")
async def get_accessibility_tree(session_id: str, query: AccessibilityTreeQuery):
    query = query.query
    if session_id in sessions:
        session = sessions[session_id]
        try:
            accessibility_tree = await session.get_accessibility_tree(query)
            return {"status": "Success", "accessibility_tree": accessibility_tree}
        except Exception as e:
            return {
                "status": "Error",
                "message": f"Error retrieving accessibility tree with query '{query.query}': {str(e)}",
            }
    else:
        return {"status": "Error", "message": "Invalid or missing session_id."}


@app.websocket("/socket")
async def websocket_endpoint(websocket: WebSocket):
    await interactive_websocket_endpoint(websocket)


# Adjust the dependency function to accept an ID
async def get_websocket_executor(websocket: WebSocket, id: str = Query(...)):
    # Now the ExecutorWebsocket is initialized with both the WebSocket and the ID
    return ExecutorWebsocket(websocket, id)


@app.websocket("/execute")
async def websocket_endpoint(
    executor: ExecutorWebsocket = Depends(get_websocket_executor),
):
    await executor.connect()
    await executor.receive_and_send()


app.include_router(extractor_router)


@app.get("/")
def read_root():
    return {"Welcome to our API :-)"}


# uvicorn main:app

# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
