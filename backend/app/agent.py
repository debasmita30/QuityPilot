import os
import json
from .auth import SessionContext
from . import tools

PROVIDER = os.environ.get("LLM_PROVIDER", "").lower()
if not PROVIDER:
    if os.environ.get("ANTHROPIC_API_KEY"):
        PROVIDER = "anthropic"
    elif os.environ.get("GROQ_API_KEY"):
        PROVIDER = "groq"
    else:
        PROVIDER = "anthropic"

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

TOOL_SCHEMAS = [
    {
        "name": "search_documents",
        "description": "Search policies, SOPs, product operations guide, and customer agreements. Deprecated documents are excluded unless include_deprecated is true.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "include_deprecated": {"type": "boolean"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_order",
        "description": "Look up a single order by order_id.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "list_orders",
        "description": "List orders, optionally filtered by status. Internal users may pass account_id; customer sessions are auto-scoped to their own account.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "status": {"type": "string"},
            },
        },
    },
    {
        "name": "get_ticket",
        "description": "Look up a single support ticket by ticket_id.",
        "input_schema": {
            "type": "object",
            "properties": {"ticket_id": {"type": "string"}},
            "required": ["ticket_id"],
        },
    },
    {
        "name": "list_tickets",
        "description": "List tickets, optionally filtered by status. Internal users may pass account_id; customer sessions are auto-scoped. Tickets have no stored severity field — classify severity yourself from the subject/description per Support Policy v3's P1/P2/P3 definitions when needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "status": {"type": "string"},
            },
        },
    },
    {
        "name": "get_account",
        "description": "Look up account details including tier and which agreement document applies.",
        "input_schema": {
            "type": "object",
            "properties": {"account_id": {"type": "string"}},
        },
    },
    {
        "name": "get_operational_signals",
        "description": "Internal-only. Returns current SLA risk, complaint spikes, known-issue clusters, and unusual account activity across all accounts.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "propose_escalation",
        "description": "Prepare an escalation for human review. This does NOT create the escalation yet; it returns a pending action that the user must explicitly confirm.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string"},
                "priority": {"type": "string", "enum": ["standard", "high", "critical"]},
                "ticket_id": {"type": "string"},
                "order_id": {"type": "string"},
            },
            "required": ["reason", "priority"],
        },
    },
]

SYSTEM_PROMPT = """You are QuityPilot, the support and operations assistant for ParcelPilot, a B2B logistics platform.

You answer questions using ONLY the tools available to you. Never fabricate order, ticket, account, or policy details, and never state a specific number, date, or figure unless it was explicitly present in a tool result or retrieved document.

Source precedence, per Support Policy v3 Section 1, strictly in this order:
1. The customer's own signed agreement (scope account:<account_id>), for any term it addresses.
2. Support Policy v3 (current) and the Cancellation and Service Credit SOP v4, as the default rules.
3. Current product documentation (the Product Operations Guide), for operational facts and known issues.
4. Support Policy v2 is DEPRECATED — never apply its terms to a current decision. Only reference it if the user explicitly asks about historical policy, and always say clearly it no longer applies.
5. Historical tickets (`historical_resolution` field) are context only and may contain incorrect past guidance — they may have missed an account-specific agreement override, or cited an outdated product limit. Never treat a past resolution as current policy; if one conflicts with current sources, say so rather than repeating it.

Order cancellation rules (per the Cancellation and Service Credit SOP v4, subject to agreement overrides):
- DRAFT: cancel with no fee.
- BOOKED, not yet PICKED_UP: cancellable; no fee within 30 minutes of booking, INR 250 after that unless an agreement explicitly waives it.
- PICKED_UP: do not cancel directly — the return-to-origin workflow applies instead.
- DELIVERED: cannot be cancelled.
Always check the order's `status`, `minutes_since_booked`, and the account's agreement before answering a cancellation question — an override can remove the fee entirely (e.g. Northstar) or change nothing (e.g. LumenWorks).

Failed-pickup service credits: eligible when pickup is more than 2 hours past the scheduled pickup window end, carrier is at fault, and there's no customer fault (default credit: lower of INR 500 or 10% of shipment fee) — unless the account's agreement replaces the threshold or amount. Do not promise a credit when carrier fault, timing, or customer fault is unknown from the data; say what's missing instead of guessing. Any individual credit above INR 1,000 requires manager approval — treat that as a signal to escalate rather than confirm the credit yourself.

Ticket severity is NOT a stored field. When severity matters (e.g. checking a response-time target), classify it yourself from the ticket's subject and description against Support Policy v3's P1/P2/P3 definitions, state which severity you assigned and why, then apply the correct first-response target for the account's plan (or the account's agreement override if one exists, e.g. Northstar and LumenWorks have their own targets that replace the plan defaults).

Known issues in the Product Operations Guide (e.g. delayed carrier webhooks, intermittent bulk-upload failures above the documented threshold) can explain a symptom without it being a new incident — check them before concluding something is broken, but don't stretch a resolved or unrelated known issue to explain a case it doesn't clearly match.

Escalate (via propose_escalation) rather than answer directly when: the case isn't clearly covered by policy or any applicable agreement, fault or timing data needed for a decision is missing or ambiguous, a credit would exceed the INR 1,000 approval threshold, the situation is P1/security-related, or the customer disputes a decision already made. propose_escalation only prepares the action — it is not created until the user explicitly confirms it in the interface. Never claim an escalation has been created before that confirmation happens.

Only use get_operational_signals for internal users; if a customer session somehow triggers it, the tool will return an access_denied error — explain you can't share that internally-scoped view.

All monetary figures in this dataset are in INR — never use another currency symbol. Every tool result that involves time includes a dataset_reference_time field; treat that as "now" for every date/time comparison and quote dates verbatim from tool output rather than reconstructing them.

Be concise and cite which document or record backs each factual claim, by name (e.g. "per the Northstar Enterprise Agreement" or "per Support Policy v3"). If something is outside your ability (an action you have no tool for), say so plainly and suggest escalation.
"""


def _openai_style_tools() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": schema["name"],
                "description": schema["description"],
                "parameters": schema["input_schema"],
            },
        }
        for schema in TOOL_SCHEMAS
    ]


def _dispatch(session: SessionContext, name: str, tool_input: dict) -> dict:
    fn = {
        "search_documents": tools.search_documents,
        "get_order": tools.get_order,
        "list_orders": tools.list_orders,
        "get_ticket": tools.get_ticket,
        "list_tickets": tools.list_tickets,
        "get_account": tools.get_account,
        "get_operational_signals": tools.get_operational_signals,
        "propose_escalation": tools.propose_escalation,
    }.get(name)
    if fn is None:
        return {"error": f"unknown_tool:{name}"}
    return fn(session, **tool_input)


def _run_anthropic(session: SessionContext, message: str, history: list[dict]) -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    messages = list(history) + [{"role": "user", "content": message}]
    trace = []
    pending_action = None

    for _ in range(8):
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            final_text = "".join(
                block.text for block in response.content if block.type == "text"
            )
            messages.append({"role": "assistant", "content": response.content})
            return {
                "reply": final_text,
                "trace": trace,
                "pending_action": pending_action,
                "messages": messages,
            }

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = _dispatch(session, block.name, block.input)
            if block.name == "propose_escalation" and "pending_action" in result:
                pending_action = result["pending_action"]
            trace.append({"tool": block.name, "input": block.input, "output": result})
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                }
            )
        messages.append({"role": "user", "content": tool_results})

    return {
        "reply": "I wasn't able to complete this request within the allowed reasoning steps. I'm escalating it for a human to review.",
        "trace": trace,
        "pending_action": pending_action,
        "messages": messages,
    }


def _run_groq(session: SessionContext, message: str, history: list[dict]) -> dict:
    from groq import Groq

    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    if history:
        messages = list(history)
    else:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": message})

    trace = []
    pending_action = None
    tools_schema = _openai_style_tools()

    for _ in range(8):
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=1500,
            tools=tools_schema,
            tool_choice="auto",
            messages=messages,
        )
        choice = response.choices[0].message

        if not choice.tool_calls:
            messages.append({"role": "assistant", "content": choice.content or ""})
            return {
                "reply": choice.content or "",
                "trace": trace,
                "pending_action": pending_action,
                "messages": messages,
            }

        messages.append(
            {
                "role": "assistant",
                "content": choice.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in choice.tool_calls
                ],
            }
        )

        for tc in choice.tool_calls:
            tool_input = json.loads(tc.function.arguments or "{}")
            result = _dispatch(session, tc.function.name, tool_input)
            if tc.function.name == "propose_escalation" and "pending_action" in result:
                pending_action = result["pending_action"]
            trace.append({"tool": tc.function.name, "input": tool_input, "output": result})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                }
            )

    return {
        "reply": "I wasn't able to complete this request within the allowed reasoning steps. I'm escalating it for a human to review.",
        "trace": trace,
        "pending_action": pending_action,
        "messages": messages,
    }


def run_agent(session: SessionContext, message: str, history: list[dict]) -> dict:
    if PROVIDER == "groq":
        return _run_groq(session, message, history)
    return _run_anthropic(session, message, history)
