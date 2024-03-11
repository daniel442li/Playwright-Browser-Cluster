from pydantic import BaseModel
from typing import Optional

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


class AccessibilityTreeQuery(BaseModel):
    query: str = ""