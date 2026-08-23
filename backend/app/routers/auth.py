from fastapi import APIRouter
from ..schemas import LoginRequest, LoginResponse
from ..auth import issue_token, decode_token
from ..database import get_conn

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/accounts")
def list_accounts():
    conn = get_conn()
    rows = conn.execute("SELECT account_id, name, tier FROM accounts").fetchall()
    conn.close()
    return {"accounts": [dict(r) for r in rows]}


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    token = issue_token(req.persona, req.account_id, req.role or "", req.display_name)
    ctx = decode_token(token)
    return LoginResponse(
        token=token,
        persona=ctx.persona,
        account_id=ctx.account_id,
        role=ctx.role,
        display_name=ctx.display_name,
    )
