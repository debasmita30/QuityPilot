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
        "description": "List tickets, optionally filtered by status, category, severity. Internal users may pass account_id; customer sessions are auto-scoped.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "status": {"type": "string"},
                "category": {"type": "string"},
                "severity": {"type": "string"},
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

You answer questions using ONLY the tools available to you. Never fabricate order, ticket, account, or policy details.

Source authority, strictly in this order:
1. A customer's specific agreement document (scope account:<name>) overrides general policy for that customer on any term it addresses.
2. Support Policy v3 (current) and the Cancellation and Service Credit SOP v4 are the default rules when no agreement override exists.
3. The Product Operations Guide provides operational facts, including known issues that affect fault determination.
4. Support Policy v2 is DEPRECATED. Never apply its terms to a current decision. Only reference it if the user is explicitly asking about historical policy or a past ticket's context, and always say clearly that it no longer applies.
5. Past ticket resolution_notes are context only and may be wrong (they may reflect deprecated policy or an incorrect goodwill decision). Never treat a past resolution as a source of current policy. If a past resolution conflicts with current policy, point that out rather than repeating it.

When answering questions that involve fees, credits, or eligibility:
- Look up the relevant order/ticket/account first.
- Search documents for the applicable agreement AND the general policy/SOP, so you can check whether an override applies.
- Do the arithmetic yourself from the retrieved facts. Show the governing source for your answer.
- If sources genuinely conflict, or the situation isn't clearly covered, say so explicitly and escalate rather than guessing.

Escalate (via propose_escalation) rather than answer directly when: the case isn't clearly covered by policy, fault is genuinely ambiguous, a requested credit exceeds the applicable approval threshold, or the customer disputes a decision already made. propose_escalation only prepares the action — it is not created until the user explicitly confirms it in the interface. Never claim an escalation has been created before that confirmation happens.

Only use get_operational_signals for internal users; if a customer session somehow triggers it, the tool will return an access_denied error — explain you can't share that internally-scoped view.

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
