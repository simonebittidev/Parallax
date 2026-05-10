# Parallax

**Parallax** is an application designed for reflection and dialogue. Users can submit a thought, opinion, or short text, and Parallax will rewrite it from three distinct perspectives: **Opposite**, **Neutral**, and **Empathetic**.

![image](https://github.com/user-attachments/assets/5f481128-70c9-4c56-a0e3-854033a92162)

This helps users:
- Explore nuance and opposing viewpoints
- Gain clarity on complex ideas
- Train for respectful and constructive discussions

---

## Table of Contents

- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Multi-Agent System](#multi-agent-system)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [CI/CD](#cicd)
- [Roadmap](#roadmap)

---

## How It Works

Parallax has two main phases: **perspective generation** and **multi-agent chat**.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER FLOW                                   │
│                                                                     │
│  1. Write an opinion                                                │
│     "I think remote work makes people less productive."             │
│                                                                     │
│  2. Select a perspective                                            │
│     [ Opposite ]  [ Neutral ]  [ Emphatic ]                        │
│                                                                     │
│  3. Parallax rewrites the text from that point of view              │
│     Opposite  → "Remote work actually boosts productivity…"         │
│     Neutral   → "Studies on remote work show mixed results…"        │
│     Emphatic  → "It's understandable to feel this way; many        │
│                  workers struggle with focus at home…"              │
│                                                                     │
│  4. Start a chat with the AI that holds that perspective            │
│                                                                     │
│  5. Add other perspectives at any time with the + buttons           │
│     → multiple AI agents debate in real-time via WebSocket          │
│                                                                     │
│  6. Direct a message to a specific agent with @Opposite,            │
│     @Neutral, or @Emphatic                                          │
└─────────────────────────────────────────────────────────────────────┘
```

### The Three Perspectives

| Perspective | Color | Behaviour |
|-------------|-------|-----------|
| **Opposite** | 🔴 Red | Takes the exact opposite stance; never yields |
| **Neutral** | 🔵 Blue | Fact-based, objective, describes without judging |
| **Emphatic** | 🟢 Green | Focuses on emotions and shared human experience |

---

## Architecture

Parallax is a full-stack application where a FastAPI backend serves both the REST/WebSocket API and the statically exported Next.js frontend.

```
┌──────────────────────────────────────────────────────────────────────┐
│                         PARALLAX SYSTEM                              │
│                                                                      │
│   Browser (Next.js SPA)                                              │
│   ┌──────────────────────────────────────────────┐                   │
│   │  page.tsx          chat.tsx                  │                   │
│   │  ┌─────────────┐   ┌────────────────────┐    │                   │
│   │  │ Text input  │   │ Chat UI            │    │                   │
│   │  │ Perspective │   │ ┌────────────────┐ │    │                   │
│   │  │ selector    │   │ │ WebSocket      │ │    │                   │
│   │  │             │   │ │ connection     │ │    │                   │
│   │  │ POST        │   │ │ @mention       │ │    │                   │
│   │  │ /api/       │   │ │ autocomplete   │ │    │                   │
│   │  │ processpov  │   │ │ typing events  │ │    │                   │
│   │  └─────────────┘   │ └────────────────┘ │    │                   │
│   │  Firebase Auth     └────────────────────┘    │                   │
│   └──────────────────────────────────────────────┘                   │
│              │  HTTPS/WSS                                            │
│   ┌──────────▼─────────────────────────────────────┐                 │
│   │            FastAPI  (app.py)                   │                 │
│   │                                                │                 │
│   │  POST /api/processpov                          │                 │
│   │   └─ create_pov()  →  Azure OpenAI GPT-4.1     │                 │
│   │                                                │                 │
│   │  WS  /ws/{user_id}/{conversation_id}           │                 │
│   │   └─ GraphExecutor.trigger_agents()            │                 │
│   │                                                │                 │
│   │  GET /messages/{user_id}/{conversation_id}     │                 │
│   │   └─ Firestore chat history                    │                 │
│   │                                                │                 │
│   │  GET /{path}  →  serves client/out (Next.js)   │                 │
│   └────────────────────────────────────────────────┘                 │
│              │                          │                            │
│   ┌──────────▼────────┐    ┌────────────▼────────────┐               │
│   │  Azure OpenAI     │    │  Firebase / Firestore   │               │
│   │  (GPT-4.1)        │    │                         │               │
│   │  via LangChain    │    │  collection: chat-history│               │
│   └───────────────────┘    └─────────────────────────┘               │
└──────────────────────────────────────────────────────────────────────┘
```

### Request Flow: Generating a Perspective

```
Browser                  FastAPI             Azure OpenAI
  │                         │                     │
  │  POST /api/processpov   │                     │
  │  { perspective,         │                     │
  │    userText, userId }   │                     │
  │────────────────────────>│                     │
  │                         │  create_pov()        │
  │                         │─────────────────────>│
  │                         │                     │  GPT-4.1 rewrites
  │                         │<─────────────────────│  the text
  │                         │                     │
  │                         │  Save to Firestore   │
  │                         │  Create ActiveAgent  │
  │                         │                     │
  │  { conv_id, pov }       │                     │
  │<────────────────────────│                     │
  │                         │                     │
  │  Redirect → /chat       │                     │
  │                         │                     │
```

### Request Flow: Chat Session

```
Browser                  FastAPI             LangGraph          Firestore
  │                         │                    │                  │
  │  WS /ws/{uid}/{cid}     │                    │                  │
  │────────────────────────>│                    │                  │
  │  { text: "..." }        │                    │                  │
  │────────────────────────>│                    │                  │
  │                         │  GraphExecutor     │                  │
  │                         │  .trigger_agents() │                  │
  │                         │───────────────────>│                  │
  │                         │                    │  Load history    │
  │                         │                    │─────────────────>│
  │                         │                    │                  │
  │  { event: "typing",     │                    │  Agent A thinks  │
  │    agent_name: "Opp" }  │                    │  (GPT-4.1)       │
  │<────────────────────────│<───────────────────│                  │
  │                         │                    │  Save message    │
  │  [ full messages array ]│                    │─────────────────>│
  │<────────────────────────│<───────────────────│                  │
  │                         │                    │                  │
  │  (repeat for each agent │                    │                  │
  │   up to max_iterations) │                    │                  │
  │                         │                    │                  │
```

---

## Multi-Agent System

The heart of Parallax is a LangGraph-based state machine that orchestrates multiple AI agents. Each agent holds a specific point of view and decides autonomously whether to contribute to the conversation.

### LangGraph State Machine

```
                     ┌─────────────┐
                     │    START    │
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
               ┌─────│  Agent A   │──────┐
               │     │ (Opposite) │      │
               │     └─────────────┘      │
               │                          │
               │  should_continue?        │
               │  iteration_count <       │
               │  max_iterations          │
               │  (random 1–4)            │
               │                          │
               ▼  True             False  ▼
        ┌──────────────┐          ┌──────────┐
        │   Agent B    │          │   END    │
        │  (Neutral)   │          └──────────┘
        └──────┬───────┘
               │
               │  should_continue?
               │
               ▼  True             False
        ┌──────────────┐          ┌──────────┐
        │   Agent C    │          │   END    │
        │  (Emphatic)  │          └──────────┘
        └──────┬───────┘
               │
               │  should_continue?
               │
               └──────► back to Agent A  ──► END
```

Each agent follows these rules:
- It **always defends its assigned point of view**, even against the user
- It **skips responding** if it has nothing to add (returns `None`)
- It **never responds** if the last message was its own
- It **prioritises responding** if its name is explicitly mentioned
- It sends a **"typing…" event** via WebSocket before broadcasting its message
- A random sleep of **1–4 seconds** between messages simulates human timing

### Agent Classes

```
ChatAgent (abstract base)
├── OppositeChatAgent   → agent_name = "Opposite"
├── NeutralChatAgent    → agent_name = "Neutral"
└── EmphaticChatAgent   → agent_name = "Emphatic"
```

Each agent uses structured output (`Result`) so the LLM is forced to return either a message or `null`, avoiding empty or noise responses.

---

## Project Structure

```
Parallax/
│
├── app.py                      # FastAPI entry point
│                               # REST endpoints + WebSocket + static serving
│
├── requirements.txt            # Python dependencies
├── azure_pipelines.yml         # Azure DevOps CI/CD pipeline
│
├── llm_utils/
│   ├── graph_executor.py       # LangGraph state machine + WebSocket broadcasting
│   ├── llm_pov.py              # Perspective generation (create_pov)
│   ├── llm_chat.py             # Agent classes (Opposite, Neutral, Emphatic)
│   ├── agentv2.py              # Parallel agent variant (experimental)
│   └── agent.py                # Sequential agent variant (legacy)
│
├── utils/
│   └── chat.py                 # Chat history serialisation helpers
│
├── templates/                  # Legacy Jinja2 templates (pre-Next.js)
│   ├── landing.html
│   └── tryout.html
│
└── client/                     # Next.js frontend
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx         # Home page (text input + perspective selector)
    │   │   ├── layout.tsx       # Root layout
    │   │   └── globals.css
    │   ├── components/
    │   │   ├── chat.tsx         # Full chat UI with WebSocket + @mention
    │   │   ├── navbar.tsx
    │   │   ├── footer.tsx
    │   │   ├── login-alert.tsx
    │   │   ├── error-alert.tsx
    │   │   └── cookie-widget.tsx
    │   └── lib/
    │       └── firebase.ts      # Firebase client initialisation + auth helpers
    ├── package.json
    ├── next.config.ts           # output: 'export' (static build)
    └── tsconfig.json
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11, Uvicorn / Gunicorn |
| AI | Azure OpenAI GPT-4.1 via LangChain |
| Agent orchestration | LangGraph (StateGraph) |
| Database | Firebase Firestore (chat history) |
| Authentication | Firebase Authentication |
| Real-time communication | WebSocket (FastAPI native) |
| CI/CD | Azure Pipelines |
| Hosting | Azure App Service (Linux) |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- An Azure OpenAI resource with a `gpt-4.1` deployment
- A Firebase project (Firestore + Authentication enabled)

### 1. Clone the repository

```bash
git clone https://github.com/simonebittidev/parallax.git
cd parallax
```

### 2. Backend setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file in the root directory (see [Environment Variables](#environment-variables)).

### 3. Frontend setup

```bash
cd client
npm install
```

Create a `.env.local` file inside `client/` with the Firebase client-side variables (see below).

```bash
npm run build          # produces client/out — the static export
```

### 4. Run locally

```bash
# From the project root
uvicorn app:app --reload --port 8000
```

Open `http://localhost:8000`.

---

## Environment Variables

### Backend (`/.env`)

| Variable | Description |
|---|---|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource endpoint |
| `FIREBASE_SERVICE_ACCOUNT` | Base64-encoded Firebase service account JSON |

The `FIREBASE_SERVICE_ACCOUNT` value must be the **base64 encoding** of the service account JSON downloaded from the Firebase console:

```bash
base64 -i serviceAccount.json | tr -d '\n'
```

### Frontend (`/client/.env.local`)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Firebase web API key |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Firebase auth domain |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | Firebase project ID |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | Firebase storage bucket |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Firebase messaging sender ID |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | Firebase app ID |

---

## API Reference

### `POST /api/processpov`

Generates a rewritten version of the user's text from a given perspective. Creates or extends a conversation session.

**Request body**

```json
{
  "perspective": "Opposite" | "Neutral" | "Emphatic",
  "userText": "string",
  "userId": "string",
  "convId": "string | null"
}
```

**Response**

```json
{
  "conv_id": "uuid",
  "pov": "The rewritten text from the selected perspective."
}
```

If `convId` is `null`, a new conversation is created. If a `convId` is provided, the new perspective is added to the existing conversation and the agent graph is re-triggered.

---

### `GET /messages/{user_id}/{conversation_id}`

Returns the full chat history for the given conversation.

**Response** — JSON-encoded array of messages:

```json
[
  { "role": "human", "content": "string", "agent_name": "" },
  { "role": "ai",    "content": "string", "agent_name": "Opposite" }
]
```

---

### `WS /ws/{user_id}/{conversation_id}`

Persistent WebSocket connection for real-time chat.

**Client → Server**

```json
{ "text": "Your message here" }
```

**Server → Client** (two event types)

Typing indicator:
```json
{ "event": "typing", "agent_name": "Neutral" }
```

Full message update (sent after each agent responds):
```json
"[ { \"role\": \"human\", \"content\": \"...\", \"agent_name\": \"\" }, ... ]"
```

The full message array is JSON-encoded twice (string inside JSON) — the client calls `JSON.parse` twice.

**Lifecycle** — on WebSocket disconnect, the server clears the in-memory agent state and the Firestore session for that conversation ID.

---

## CI/CD

Parallax is deployed to **Azure App Service** via **Azure Pipelines** (`azure_pipelines.yml`).

```
┌────────────────────────────────────────────────────────┐
│                  Azure Pipelines                       │
│                                                        │
│  Trigger: push to main                                 │
│                                                        │
│  Stage 1 — Build (ubuntu-latest)                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │  1. Set up Python 3.11                           │  │
│  │  2. Set up Node.js 18                            │  │
│  │  3. pip install -r requirements.txt              │  │
│  │  4. npm ci && npm run build  (Next.js → out/)    │  │
│  │     Injects NEXT_PUBLIC_* env vars from secrets  │  │
│  │  5. Zip artifact (client/out + Python files)     │  │
│  │  6. Publish artifact as "drop"                   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  Stage 2 — Deploy (depends on Build)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  AzureWebApp@1 → App Service "parallax"          │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

The Next.js frontend is compiled to a **static export** (`output: 'export'` in `next.config.ts`) and placed in `client/out`. FastAPI then serves these files directly, so the whole application runs as a single process.

---

## Roadmap

- [x] AI integration for real-time perspective generation
- [x] Multi-agent real-time chat via WebSocket
- [x] Firebase authentication
- [x] Persistent chat history (Firestore)
- [x] @mention to direct messages at a specific agent
- [ ] Multi-language support
- [ ] Conversation history page (per user)
- [ ] Export conversation as PDF or shareable link
- [ ] Mobile app

---

**Parallax** is a tool to help you understand before debating — and connect before convincing.
