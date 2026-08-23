# Product Note

## Which additional client problem I chose, and how

I chose **Problem 1: Proactive Issue Detection**, built on the same data layer as the
chatbot rather than as a separate app. Reasoning: the chatbot only helps once someone
thinks to ask, and ParcelPilot's actual complaint in the brief is that the ops team is
manually searching across sources today — a chatbot alone still requires someone to
notice something is wrong before they open it. The dashboard (`Signals`) surfaces four
concrete detectors — SLA risk, complaint spikes, cross-account known-issue clusters,
and unusual per-account ticket concentration — computed directly from the ticket data,
with deliberately simple, explainable rules (elapsed-time ratios, rolling-window
counts, keyword-based issue matching) rather than a black-box model, because a support
lead needs to trust and act on a signal immediately, and a rule they can restate in one
sentence is easier to trust on day one than a cluster score they can't interrogate.

**Problem 2 (trust and reliability)** wasn't treated as optional or separate — it's
load-bearing in the minimum requirements too (source authority, conflict handling,
escalation). The precedence model, the exclusion of deprecated documents by default,
and the explicit "past resolutions are context only" instruction are all direct
responses to it; see `ARCHITECTURE.md` for the mechanics.

## What else I'd build next, and why (roughly in priority order)

1. **A feedback loop on wrong or unclear answers.** Right now there's no way for a
   support agent to flag "this answer was wrong" back into the system. Without it, a
   source-precedence bug or a stale document ships silently. This is the highest
   priority because it's the difference between a system that degrades quietly and one
   that gets caught and fixed fast — directly serves the "trust" problem.
2. **Confidence-based auto-routing.** The agent currently escalates based on prompt
   instructions alone. A lightweight confidence signal (e.g., retrieval score spread,
   or an explicit self-rated certainty from the model) could route borderline cases to
   a queue for review even when the agent doesn't recognize the ambiguity itself,
   catching cases the prompt-based escalation logic misses.
3. **Real authentication and role scoping**, replacing the mocked session tokens with
   an actual identity provider and per-role tool permissions (e.g., support agents can
   view but not approve credits above a threshold; only ops managers can).
4. **A customer-facing surface** on the same backend, since the tool/access-control
   layer already supports a customer-scoped session — mainly a UI and prompt-tone
   variant at this point, not a rebuild.
5. **Learned signal detection** to complement the rule-based dashboard once there's
   enough historical ticket volume to validate a model against — rules are the right
   starting point, but they won't catch a pattern nobody thought to write a rule for.
6. **Structured document ingestion from real PDFs**, including versioning so a policy
   update automatically supersedes the prior version's chunks instead of relying on a
   hand-set `status` field.

## What I intentionally left out of this submission

- **Streaming responses** — the chat UI waits for a full reply; streaming would improve
  perceived latency but wasn't worth the added complexity for a first pass.
- **Multi-tenant production auth** — session tokens are signed but not backed by a real
  identity system (see above).
- **A dense/embedding retriever** — TF-IDF is adequate at this corpus size; swapping it
  in is a contained change behind the existing `retrieval.py` interface, not a rewrite.
- **Persistent conversation/action storage** — both live in memory for this demo and
  reset on restart; fine for a demo, not for production.
- **Automated retrieval quality evaluation** — I validated behavior with targeted
  manual test queries (see `ARCHITECTURE.md` / `tests/`) rather than a full golden-set
  regression harness, given time constraints; that harness is the natural next step
  before shipping changes to the precedence prompt or retrieval scoring.

## One metric I'd use to judge whether this is useful

**Unassisted resolution rate with zero post-hoc correction**: the share of chatbot
answers that a support agent (or customer) accepts without needing a human to step in,
correct, or escalate afterward — tracked separately for "answered directly" vs.
"escalated" responses, since a high escalation rate on genuinely ambiguous cases is
healthy, while a high correction rate on directly-answered cases is the signal that
actually indicates a trust problem. I'd rather under-answer and escalate than confidently
guess wrong, so I'd watch the correction rate on direct answers as the primary red flag,
not raw containment volume.
