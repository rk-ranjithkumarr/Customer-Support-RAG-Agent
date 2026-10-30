# Real-Time Customer Support RAG Agent

A working Retrieval-Augmented Generation support bot with:

- **Real-time streaming** answers over WebSocket (token by token)
- **Live knowledge base** - drop a `.md/.txt/.pdf` into `data/knowledge_base/` (or use the Upload button) and it is re-indexed automatically
- **Source citations** on every answer
- **Confidence-based escalation** - low-confidence questions or "talk to a human" create a support ticket (SQLite)
- **Conversation memory** for follow-up questions
- **Works with zero API keys** (offline extractive mode). Add an Anthropic key for full Claude answers.

## Step-by-step installation

### Step 1 - Prerequisites
Python 3.10 or newer. Check with `python --version` (or `python3 --version`).

### Step 2 - Unzip and enter the folder
```bash
unzip support-rag.zip
cd support-rag
```

### Step 3 - Create a virtual environment
```bash
python3 -m venv venv
# macOS / Linux
source venv/bin/activate
# Windows (PowerShell / cmd)
venv\Scripts\activate
```
(Steps 3-5 can be done in one go by running `./setup.sh` on Mac/Linux or `setup.bat` on Windows.)

### Step 4 - Install the libraries
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

| Library | Why |
|---|---|
| fastapi, uvicorn | Web server + WebSocket streaming |
| scikit-learn, numpy | TF-IDF retrieval (no model download) |
| anthropic | Claude LLM (optional at runtime) |
| watchdog | Real-time knowledge base file watching |
| python-dotenv | Loads `.env` settings |
| python-multipart | File uploads |
| pypdf | PDF knowledge base support |
| pytest, httpx | Tests |

### Step 5 - Configure (optional)
```bash
cp .env.example .env        # Windows: copy .env.example .env
```
Edit `.env` and set `ANTHROPIC_API_KEY=...` to get real Claude answers. Leave it blank to run offline.

### Step 6 - Run the tests (optional)
```bash
python -m pytest -q
```

### Step 7 - Start the app
```bash
python run.py
```
Open **http://127.0.0.1:8000**.

## Try it
- "How do I get a refund?"  ->  answer + sources
- "and for annual plans?" -> follow-up understood via memory
- "Talk to a human" or a random off-topic question -> ticket form appears
- Upload your own FAQ file, then ask about it immediately

## API
| Endpoint | Purpose |
|---|---|
| `GET /` | Chat UI |
| `WS /ws/chat` | Streaming chat. Send `{"message": "...", "session_id": "..."}` |
| `POST /api/chat` | Non-streaming chat (curl-friendly) |
| `POST /api/upload` | Upload a KB document |
| `POST /api/reindex` | Force re-index |
| `POST /api/tickets`, `GET /api/tickets` | Create / list support tickets |
| `GET /api/health` | Status |

```bash
curl -X POST localhost:8000/api/chat -H "Content-Type: application/json" \
  -d '{"message":"What are the API rate limits?"}'
```

## Optional: semantic embeddings
Better matching on paraphrased questions:
```bash
pip install sentence-transformers
# in .env
RETRIEVER=embeddings
```
(First run downloads the ~90 MB `all-MiniLM-L6-v2` model.)

## Customize
- Replace files in `data/knowledge_base/` with your own docs; set `COMPANY_NAME` in `.env`.
- Tune `MIN_SCORE` in `.env`: higher = escalates more often, lower = answers more often.
- Prompt rules live in `app/llm.py`; escalation logic in `app/agent.py`.

## Project layout
```
app/
  main.py       FastAPI app, WebSocket, upload, tickets API
  agent.py      retrieve -> decide -> stream, memory, escalation
  retriever.py  TF-IDF / embeddings search
  loader.py     file reading + heading-aware chunking
  llm.py        Claude streaming + offline fallback
  watcher.py    live re-indexing
  tickets.py    SQLite tickets
static/index.html   chat UI
data/knowledge_base/   sample help-center docs
tests/              pytest suite
```

## Troubleshooting
- `ModuleNotFoundError` -> the venv is not activated (Step 3).
- Port busy -> set `PORT=8001` in `.env`.
- Answers look like plain bullet lists -> no API key set (offline mode); add `ANTHROPIC_API_KEY`.
- Everything escalates -> lower `MIN_SCORE` (e.g. `0.05`) or add more docs.
