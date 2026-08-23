from fastapi import APIRouter, Depends
from ..auth import get_session, SessionContext
from .. import tools

router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/{action_id}/confirm")
def confirm(action_id: str, session: SessionContext = Depends(get_session)):
    return tools.confirm_action(session, action_id)


@router.post("/{action_id}/cancel")
def cancel(action_id: str, session: SessionContext = Depends(get_session)):
    return tools.cancel_action(session, action_id)
