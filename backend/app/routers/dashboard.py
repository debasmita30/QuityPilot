from fastapi import APIRouter, Depends, HTTPException
from ..auth import get_session, SessionContext
from ..signals import compute_signals

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/signals")
def signals(session: SessionContext = Depends(get_session)):
    if not session.is_internal:
        raise HTTPException(403, "internal users only")
    return compute_signals()
