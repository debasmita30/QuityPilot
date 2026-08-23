import uuid
from fastapi import APIRouter, Depends
from ..schemas import ChatRequest, ChatResponse
from ..auth import get_session, SessionContext
from ..agent import run_agent
from ..store import CONVERSATIONS

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest, session: SessionContext = Depends(get_session)):
    conversation_id = req.conversation_id or str(uuid.uuid4())
    history = CONVERSATIONS.get(conversation_id, [])

    result = run_agent(session, req.message, history)
    CONVERSATIONS[conversation_id] = result["messages"]

    return ChatResponse(
        conversation_id=conversation_id,
        reply=result["reply"],
        trace=result["trace"],
        pending_action=result["pending_action"],
    )
