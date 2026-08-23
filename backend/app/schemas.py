from pydantic import BaseModel


class LoginRequest(BaseModel):
    persona: str
    account_id: str | None = None
    role: str | None = None
    display_name: str


class LoginResponse(BaseModel):
    token: str
    persona: str
    account_id: str | None
    role: str
    display_name: str


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str


class ToolTraceEntry(BaseModel):
    tool: str
    input: dict
    output: dict


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    trace: list[ToolTraceEntry]
    pending_action: dict | None = None


class ActionConfirmResponse(BaseModel):
    result: dict
