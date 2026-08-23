from dataclasses import dataclass
from itsdangerous import URLSafeSerializer, BadSignature
from fastapi import Header, HTTPException

SECRET = "quitypilot-demo-secret-do-not-use-in-production"
serializer = URLSafeSerializer(SECRET, salt="session")

VALID_ACCOUNTS = {"ACCT-001", "ACCT-002", "ACCT-003", "ACCT-004"}
VALID_ROLES = {"customer", "support_agent", "ops_manager"}


@dataclass
class SessionContext:
    persona: str
    account_id: str | None
    role: str
    display_name: str

    @property
    def is_internal(self) -> bool:
        return self.persona == "internal"

    @property
    def can_approve_high_value(self) -> bool:
        return self.role == "ops_manager"


def issue_token(persona: str, account_id: str | None, role: str, display_name: str) -> str:
    if persona == "customer":
        if account_id not in VALID_ACCOUNTS:
            raise HTTPException(400, "unknown account")
        role = "customer"
    elif persona == "internal":
        if role not in {"support_agent", "ops_manager"}:
            raise HTTPException(400, "unknown role")
        account_id = None
    else:
        raise HTTPException(400, "unknown persona")

    payload = {
        "persona": persona,
        "account_id": account_id,
        "role": role,
        "display_name": display_name,
    }
    return serializer.dumps(payload)


def decode_token(token: str) -> SessionContext:
    try:
        payload = serializer.loads(token)
    except BadSignature:
        raise HTTPException(401, "invalid session")
    return SessionContext(**payload)


def get_session(authorization: str = Header(default="")) -> SessionContext:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing session token")
    token = authorization.removeprefix("Bearer ").strip()
    return decode_token(token)
