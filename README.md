<div align="center">

# 📦 QuityPilot

### An AI Support & Operations Console for ParcelPilot

*Built for the CalQuity AI Engineer Assessment*

<a href="https://quity-pilot.vercel.app/" target="_blank"> <img src="https://img.shields.io/badge/🚀%20LIVE%20DEMO-quity--pilot.vercel.app-4FE0B0?style=for-the-badge&logoColor=white" alt="Live Demo"/> </a>

![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![scikit--learn](https://img.shields.io/badge/scikit--learn-TF--IDF%20Retrieval-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)
![React](https://img.shields.io/badge/React-Vite%20%2B%20TS-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Tailwind](https://img.shields.io/badge/Tailwind%20CSS-v4-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)

![LLM](https://img.shields.io/badge/LLM-Claude%20%7C%20Groq%20(Llama%203.3%2070B)-B69CFF?style=for-the-badge)
![Access Control](https://img.shields.io/badge/Access-Account%20%2F%20Role%20Scoped-FF7A3C?style=for-the-badge)
![Human in the Loop](https://img.shields.io/badge/Escalations-Human%20Confirmed-4FE0B0?style=for-the-badge)



</div>

---

## 📌 Quick Links

| ❓ [What It Does](#-what-it-does) | 🧭 [Why Internal-First](#-why-internal-first) | 🏗️ [Stack](#-stack) |
|:---:|:---:|:---:|
| 🖼️ [Screenshots](#️-screenshots) | ⚙️ [Running Locally](#️-running-locally) | 🧪 [Try It](#-try-it) |
| 🚀 [Deployment](#-deployment) | 🗂️ [Repository Layout](#️-repository-layout) | 🤖 [AI Tool Usage](#-ai-tool-usage) |

---

## ❓ What It Does

QuityPilot is an **internal-facing agent** for ParcelPilot's support/ops team, paired with a **proactive issue-detection dashboard**. It answers natural-language questions by reasoning over policy documents, customer agreements, and structured order/ticket data.

Instead of treating every document as equally authoritative, QuityPilot **resolves conflicts between sources** — current vs. deprecated policy, general SOP vs. customer-specific agreement — and it **prepares but never executes an escalation** without explicit human confirmation.

```
Policy documents ─┐
Customer agreements ├──► Precedence-aware retrieval ──► Agent reasoning ──► Grounded answer
Order / ticket data ─┘                                         │
                                                                 └──► Escalation drafted, never auto-fired
```

## 🧭 Why Internal-First

The assessment allows either a customer-facing or an internal support/ops chatbot. QuityPilot targets the **internal user first** because:

- It lets the same backend also power **Problem 1** (proactive issue detection) without a second app.
- Internal tooling justifies richer tool use — cross-account queries, escalation creation, ticket updates — that better demonstrates multi-step agentic reasoning.
- The tool layer already supports a **customer-scoped session** (`auth.py`), so a customer-facing UI variant is a smaller follow-on rather than a from-scratch rebuild.

## 🏗️ Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI (Python), SQLite, scikit-learn (TF-IDF retrieval) |
| **Agent / LLM** | Provider abstraction — Anthropic Claude *or* Groq (free tier, Llama 3.3 70B, OpenAI-compatible tool calling) |
| **Frontend** | React + Vite + TypeScript, Tailwind CSS v4 |
| **Data** | The real ParcelPilot candidate data pack (see `NOTE_ON_DATA.md`) |

---

## 🖼️ Screenshots

<div align="center">

### Manifest-scoped sign-in — Internal Ops vs. Customer

<img width="1568" height="712" alt="login-internal" src="https://github.com/user-attachments/assets/1e34d0d4-c760-4190-b7b4-86cd5d934de2" />


*Internal roles select a role (e.g. Ops Manager) and get cross-account tools plus the Signals dashboard.*

<br/>

<img width="1568" height="704" alt="login-customer" src="https://github.com/user-attachments/assets/8a5b90fc-da3e-4f25-ab6b-e21b9515b864" />


*Customer sessions are scoped to a single seeded account at the data layer.*

<br/>

### Precedence-aware reasoning, as an Ops Manager

<img width="1568" height="707" alt="chat-internal-precedence" src="https://github.com/user-attachments/assets/fb85175a-fcdd-4bd6-94c5-a65e5d0927b6" />


*Asked whether Northstar can cancel `ORD-1001` without a fee, the agent pulls the order, checks the default Cancellation SOP (₹250 after 30 minutes), then finds the Northstar Enterprise Agreement waives the fee unconditionally — and explains why the agreement wins.*

<br/>

### The same question, scoped to a customer session

<img width="1568" height="708" alt="chat-customer-scoped" src="https://github.com/user-attachments/assets/42ebc568-3ec0-4217-afd5-82fa092724b7" />


*The identical question asked from a customer session for a different account: the order lookup is denied (`access_denied`) at the tool layer before the model ever sees that account's data — the agent still reasons over the policy text it's allowed to see, but is upfront that it can't confirm the order's current status.*

</div>

---

## ⚙️ Running Locally

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set an API key, see "Choosing a model provider" below
uvicorn app.main:app --reload --port 8000
```

### Choosing a model provider

QuityPilot works with either provider through the same `agent.py` interface, selected by `LLM_PROVIDER` in `.env` (`anthropic` or `groq`); if unset, it auto-picks based on whichever API key is present, preferring Anthropic if both are set.

| | Groq (free, recommended) | Anthropic Claude (paid) |
|---|---|---|
| **Setup** | Free key at [console.groq.com](https://console.groq.com) | `ANTHROPIC_API_KEY=sk-ant-...` |
| **.env** | `LLM_PROVIDER=groq`, `GROQ_API_KEY=gsk-...` | `LLM_PROVIDER=anthropic` |
| **Model** | `llama-3.3-70b-versatile` | Claude |
| **Notes** | Free tier is rate-limited — if you hit a limit mid-conversation, wait a few seconds and retry; that's a Groq account limit, not a bug | Higher quality tool-use reasoning |

Verify it works with a quick smoke test before relying on it for a demo — neither provider has been exercised against the live API in this build environment:

```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"persona":"internal","role":"ops_manager","display_name":"Test"}' | jq -r .token
# then, using that token:
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"message":"Can Northstar cancel ORD-1001 without a cancellation fee?"}'
```

The SQLite database is dropped and reseeded on every startup, so the demo is always in a known state.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_BASE, defaults to http://localhost:8000
npm run dev
```

Open the printed local URL. Sign in as either an internal role (support agent or ops manager) or a customer scoped to one of the four seeded accounts.

---

## 🧪 Try It

- **"Can Northstar cancel ORD-1001 without a cancellation fee? Explain why."** — tests whether the agent applies Northstar's unconditional cancellation waiver instead of the SOP's default 30-minute grace period / INR 250 fee.
- **"Should LumenWorks get a service credit for ORD-2002?"** — needs the order's carrier ID, pickup-window timing, and LumenWorks' agreement-specific INR 300 / 4-hour failed-pickup rule, which replaces the SOP's default threshold and amount.
- **"What severity is TKT-501 and is it within its response target?"** — severity isn't a stored field; the agent classifies it from the ticket text against Support Policy v3's P1/P2/P3 definitions, then applies Northstar's SLA override.
- **"Does KI-211 explain why TKT-504's order still shows BOOKED?"** — tests whether the agent uses the Product Operations Guide to avoid escalating a symptom that's already a known, monitored issue.
- **As a customer session**, ask about another account's order — the tool layer returns `access_denied` before the model ever sees that account's data.
- **Ask the agent to escalate something** — it prepares the escalation and stops; nothing is created until you click Confirm.
- **Log in as an internal user and open Signals** — it should surface TKT-501 and TKT-505 as breached (both P1s, both over their response target) and the recurring bulk-upload pattern across TKT-502 and the historical TKT-451.

---

## 🗂️ Repository Layout

```
backend/
  app/
    data/documents/     the six candidate-pack documents, transcribed to markdown
    database.py          SQLite schema + seed data (from ParcelPilot_Assessment_Data.xlsx)
    retrieval.py          document chunking, metadata tagging, precedence-aware search
    auth.py                mock session issuing/decoding, scoped to account or role
    tools.py                account-scoped tool functions (the access-control layer)
    signals.py               proactive issue detection incl. severity classification
    agent.py                  Claude/Groq tool-use loop + system prompt
    routers/                   /auth, /chat, /actions, /dashboard
frontend/
  src/
    components/    Login, ChatPanel, ToolTrace, PendingActionCard, Dashboard
    lib/api.ts       typed API client
ARCHITECTURE.md
PRODUCT.md
NOTE_ON_DATA.md
```

---

## 🚀 Deployment

**Backend does not fit Vercel's serverless model** — it keeps conversation history and pending confirmations in memory and writes to a local SQLite file, none of which survives a stateless serverless invocation. Use a host that runs it as a persistent container instead:

- **Render** — New → Web Service → point at this repo, root directory `backend` (it will use `render.yaml` / the included `Dockerfile` automatically). Set `LLM_PROVIDER`, either `GROQ_API_KEY` or `ANTHROPIC_API_KEY`, and `CORS_ORIGINS` to your Vercel domain once you have it (defaults to `*`, fine for development) — in the service's environment settings, never committed to the repo.
- **Railway or Fly.io** work the same way with the same `Dockerfile`.
- Free tiers on these typically spin down when idle — hit `/health` a minute before a live demo to warm the instance back up.

**Frontend fits Vercel well** — it's a static Vite build with no server-side state. Import the repo, set root directory to `frontend`, and set `VITE_API_BASE` to your deployed backend's URL.

---

## 🤖 AI Tool Usage

Built with Claude (Anthropic) as a pair-programmer for scaffolding, boilerplate, and first drafts of the retrieval/access-control/agent logic, with manual review and editing throughout — see `PRODUCT.md` for specifics.

<div align="center">

---

*Precedence-aware reasoning · account-scoped access · human-confirmed escalations*

</div>
