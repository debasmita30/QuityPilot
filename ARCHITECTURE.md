# Architecture Note

## Agent design

QuityPilot uses a single agent, run as an explicit tool-use loop (`agent.py:
run_agent`) rather than a one-shot function call: the model is given tool results and
allowed to re-plan, up to 8 tool-use rounds, until it produces a final text response or
the round limit is hit (at which point the system degrades to an explicit escalation
message rather than a silent failure).

The loop is implemented against two interchangeable providers behind the same
function signature: Anthropic's Messages API (native tool-use blocks) and Groq's
OpenAI-compatible chat completions API (function-calling with Llama 3.3 70B). A single
`TOOL_SCHEMAS` list, written once in Anthropic's schema shape, is converted to the
OpenAI function-calling shape for Groq (`_openai_style_tools`) so tool definitions
never drift between providers. Provider selection is an environment variable
(`LLM_PROVIDER`, or auto-detected from whichever API key is set) rather than a
compile-time choice, because Anthropic gives materially better tool-use reasoning but
Groq's free tier makes the system runnable and demoable at zero cost — a real
trade-off worth exposing, not hiding.

The system prompt encodes the source-precedence rules and escalation criteria directly
(see below) — this is deliberate: precedence is a judgment call that needs to be
visible and auditable in one place, not scattered across retrieval-time heuristics the
prompt has no visibility into. Retrieval-time filtering (excluding deprecated docs,
boosting account-specific scope) narrows what the model *can* cite; the prompt governs
how it reasons over what it's given. Both layers matter — filtering alone doesn't stop
the model from reasoning incorrectly about ambiguous cases, and prompting alone doesn't
stop it from being handed the wrong source in the first place.

Conversation state is kept server-side, keyed by a `conversation_id` the frontend holds
onto and replays with each turn, rather than trusting the client to resend full message
history — this keeps the session token as the only thing the client needs to carry, and
means tool outputs (which may include account-scoped data) never round-trip through the
browser as conversation state.

## Tool design

Four tool categories, chosen to force real multi-step composition rather than one tool
per possible question:

1. **`search_documents`** — retrieval over policy/SOP/agreement/product-ops content.
2. **Structured lookups** (`get_order`, `list_orders`, `get_ticket`, `list_tickets`,
   `get_account`) — deliberately return raw facts (e.g. `hours_until_pickup`,
   `hours_since_created`) rather than pre-computed business decisions. The tools do not
   decide whether a fee is waived or an SLA is breached — that requires combining a
   structured fact with a document's stated rule, which is the model's job. Baking the
   full decision into a tool would make the "multi-step reasoning" requirement
   cosmetic, since the agent would just be relaying a Python function's answer.
3. **`get_operational_signals`** — internal-only aggregation over the ticket data,
   shared with the `Problem 1` dashboard so the two surfaces can't drift apart.
4. **`propose_escalation`** — the state-changing tool. It only ever creates a
   `pending_confirmation` object held server-side in memory; it never writes to the
   database. A confirmed action requires a second, separate authenticated call to
   `POST /actions/{id}/confirm`, triggered by an explicit UI action, not by the model
   or by parsing the user's chat text for words like "yes." This was a specific design
   choice: confirming via chat text is easy to spoof (a document or a prior message
   could contain something that reads as confirmation); a distinct button bound to a
   specific `action_id` cannot be triggered by conversation content.

## Document and structured-data handling

Documents are Markdown with YAML frontmatter (`doc_id`, `status`, `scope`,
`effective_date`) standing in for the real PDFs (see `NOTE_ON_DATA.md`), chunked by
heading, and indexed with TF-IDF (`scikit-learn`) rather than a dense embedding model.
This was a deliberate trade-off for this dataset size: the corpus is small enough and
the vocabulary specific enough (defined terms like "service credit," "cancellation
fee," "SLA") that keyword-sensitive retrieval outperforms semantic similarity alone
and needs no external embedding API or model download. `retrieval.py` is written so a
dense or hybrid retriever is a drop-in replacement behind the same `search()`
interface if the corpus grows past what TF-IDF handles well.

Retrieval applies two independent adjustments on top of raw similarity: deprecated
documents are excluded unless the caller explicitly asks to include them (used only
when a query is clearly about historical context), and chunks scoped to the requesting
account are boosted while chunks scoped to a *different* account are heavily
down-weighted — so a Northstar session's query naturally surfaces the Northstar
agreement first without the model needing to know to ask for it by name.

Structured data lives in SQLite, recreated from a fixed seed on every process start so
demos are reproducible. All account-scoped queries take their scope from the
authenticated session (`SessionContext.account_id`), not from any parameter the model
supplies — see Access Control below.

## Source reliability and conflict handling

Precedence, as encoded in the system prompt and mirrored in retrieval boosting:

1. A customer's own agreement, for any term it addresses.
2. Current general policy (`support_policy_v3`) and the cancellation/credit SOP as the
   default.
3. The product ops guide for operational facts (e.g. whether a given delay pattern
   counts as carrier fault).
4. The deprecated policy — never authoritative, referenced only for historical
   context and always flagged as superseded when it comes up.
5. Past ticket `resolution_notes` — context only, explicitly may be wrong, never
   treated as a policy source. The agent is instructed to flag rather than repeat a
   past resolution that conflicts with current policy.

When the sources that survive this precedence ordering still conflict, or a case falls
outside what any of them cover, the agent is instructed to say so explicitly and use
`propose_escalation` rather than pick an answer. This is the main lever against
"confidently incorrect" output, alongside always naming which document backed a given
answer so a human can spot-check it in one glance.

## Access control

Enforced in `tools.py`, not in the prompt. Every account-scoped tool function takes its
scope from `SessionContext` (built from a signed session token, decoded server-side)
rather than from any `account_id` argument the model might pass — for customer
sessions, an `account_id` argument is ignored entirely in favor of the session's own
account; for internal sessions, a supplied `account_id` is validated against the known
account list before use. A customer session asking about another account's order gets
a tool-level `access_denied` result, which the model then has to explain — it cannot
retrieve the data to leak it, because the tool layer never returns it. This was tested
directly (`tools.get_order` cross-account call in `tests/`) rather than only relied
on via prompt instructions.

## Major trade-offs

- **Groq (free tier) as the default provider over Anthropic** — makes the system
  runnable without a paid API key, at the cost of a much tighter tokens-per-minute
  budget and generally weaker multi-step tool-use judgment than Claude on genuinely
  ambiguous cases. The system prompt and tool set are identical either way, so
  switching to Anthropic for a higher-stakes demo is a one-line env change.
- **TF-IDF over embeddings** — faster to stand up, no external dependency, adequate
  for a policy-document corpus this size; would move to a hybrid retriever with real
  volume.
- **In-memory pending actions and conversation state** — fine for a single-process
  demo; a production version needs these in a shared store (Redis/Postgres) to survive
  restarts and scale past one process.
- **Mocked authentication** — session tokens are signed but not tied to a real identity
  provider; sufficient to demonstrate the enforcement pattern, not production auth.
- **Deterministic detection rules over ML clustering for Problem 1** — chosen for
  explainability; the trade-off is missing subtler patterns a learned model might
  catch, discussed further in `PRODUCT.md`.
