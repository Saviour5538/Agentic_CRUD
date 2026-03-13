# 🤖 Agentic CRUD

> A multi-agent AI pipeline that autonomously builds a fully functional CRUD web application from a single plain-English problem statement.

---

## 📌 Overview

Agentic CRUD is a proof-of-concept that validates whether a structured multi-agent workflow can consistently produce working, testable software. The entire process — requirements gathering, architecture design, sprint planning, coding, and quality review — is handled by specialised AI agents coordinated by LangGraph. Zero manual coding required.

---

## 🏗️ Architecture

The pipeline runs 7 stages in sequence. Stages 4 and 5 (Dev and QA) form a feedback loop that repeats up to 3 times per task before force-advancing.

```
🔵 BA Agent → 🟣 Architect → 🟡 PM Agent → 🟢 Dev Agent ↔ 🔴 QA Agent → ⚙️ advance_task → ✅ UAT
```

| Stage | Agent | Role |
|---|---|---|
| 1 | BA Agent | Converts problem statement to structured SOW |
| 2 | Architect Agent | Designs DB schema, file structure, ER diagram |
| 3 | PM Agent | Breaks architecture into 6-8 ordered sprint tasks |
| 4 | Dev Agent | Writes complete app.py for each sprint task |
| 5 | QA Agent | Reviews code — pass or fail with feedback |
| 6 | advance_task | Increments task index, resets loop counter |
| 7 | UAT / END | Human acceptance testing handoff |

---

## 🧰 Tech Stack

| Tool | Role |
|---|---|
| LangGraph | Orchestration engine — handles the Dev/QA loop |
| LangChain | Agent toolkit — prompt templates, LLM wrappers |
| Groq API | Ultra-fast cloud LLM inference |
| Streamlit | Generated app UI |
| SQLite | Generated app database |
| python-dotenv | API key management |

---

## 🤖 Models Used

| Agent | Model | Reason |
|---|---|---|
| BA Agent | `llama-3.1-8b-instant` | Simple JSON output, token efficient |
| Architect Agent | `moonshotai/kimi-k2-instruct` | Strong at technical design |
| PM Agent | `llama-3.1-8b-instant` | Simple task list generation |
| Dev Agent | `llama-3.3-70b-versatile` | Complex code generation |
| QA Agent | `meta-llama/llama-4-scout-17b-16e-instruct` | Code review, separate token pool |

Using multiple models spreads token usage across different daily limits, preventing rate limit crashes mid-pipeline.

---

## 📁 Project Structure

```
Agentic_CRUD/
├── .env                        # Groq API key — never commit this
├── main.py                     # LangGraph graph definition and entry point
├── state.py                    # ProjectState TypedDict — shared agent memory
├── requirements.txt            # All pip dependencies
│
├── agents/
│   ├── __init__.py             # LLM instances for each agent
│   ├── ba_agent.py             # Business Analyst — generates SOW
│   ├── architect_agent.py      # Architect — designs DB schema + file structure
│   ├── pm_agent.py             # Project Manager — creates WBS task list
│   ├── dev_agent.py            # Developer — writes app.py code
│   └── qa_agent.py             # QA Engineer — reviews code, pass or fail
│
├── tools/
│   ├── __init__.py
│   ├── file_ops.py             # write_file / read_file / list_files
│   └── logger.py               # JSON pipeline log writer
│
└── generated_workspace/
    ├── app.py                  # Final CRUD app produced by agents
    ├── architecture.md         # Full DB schema + Mermaid ER diagram
    └── pipeline_log.json       # Complete run log with token usage
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10 or higher
- A Groq API key — free tier at [console.groq.com](https://console.groq.com)

### Step-by-Step

**1. Clone and navigate to the project:**
```bash
git clone <your-repo-url>
cd Agentic_CRUD
```

**2. Create and activate a virtual environment:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Install dependencies:**
```bash
pip install langgraph langchain-groq streamlit python-dotenv
```

**4. Add your Groq API key to `.env`:**
```
GROQ_API_KEY=your_actual_groq_api_key_here
```

**5. Verify installation:**
```bash
python -c "import langgraph, langchain_groq, streamlit; print('All OK')"
```

---

## 🚀 How to Run

### Run the Pipeline
```bash
python main.py
```

### Run the Generated App
```bash
streamlit run generated_workspace/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### Force Regenerate
```bash
# Windows
del tasks.db
del generated_workspace\app.py
del generated_workspace\pipeline_log.json
python main.py

# macOS / Linux
rm tasks.db generated_workspace/app.py generated_workspace/pipeline_log.json
python main.py
```

---

## 🔄 Changing the App

To build a different app, change one line in `main.py`:

```python
# Current
"problem_statement": "Build a basic Task Management CRUD app",

# Examples
"problem_statement": "Build a To Do app"
"problem_statement": "Build a student grade tracker"
"problem_statement": "Build an expense tracker with categories and monthly reports"
```

No other changes needed. The entire pipeline adapts automatically.

---

## 📊 Pipeline Log

After each run, `generated_workspace/pipeline_log.json` contains:

```json
{
  "run_started_at": "2026-03-13 10:00:00",
  "problem_statement": "Build a basic Task Management CRUD app",
  "stages": {
    "ba_agent": {
      "in_scope": ["User authentication", "Task creation", "..."],
      "out_scope": ["Advanced reporting", "..."],
      "tokens": { "prompt": 129, "completion": 185, "total": 314 }
    },
    "architect_agent": {
      "database_schema": "...",
      "mermaid_diagram": "erDiagram ...",
      "tokens": { "prompt": 267, "completion": 296, "total": 563 }
    }
  },
  "dev_qa_cycles": [
    {
      "task_index": 1,
      "task_name": "Create Users table",
      "iteration": 1,
      "status": "qa_passed",
      "issues": []
    }
  ],
  "run_completed_at": "2026-03-13 10:05:00"
}
```

---

## 🏗️ ER Diagram

After each run, open `generated_workspace/architecture.md` to view the full database schema and ER diagram. Paste the Mermaid diagram at [mermaid.live](https://mermaid.live) to visualise it.

---

## 🔁 Dev / QA Feedback Loop

```
Dev Agent writes app.py
        ↓
QA Agent reviews (syntax check + LLM review)
        ↓
    Passed? ──Yes──→ advance_task → next task
        │
       No
        │
  iteration < 3? ──Yes──→ Dev Agent retries with feedback injected
        │
       No
        ↓
  Force advance (prevents infinite loop)
```

---

## ⚠️ Rate Limiting

Groq free tier: **100,000 tokens/day** per model. The pipeline handles 429 errors automatically:

```
⏳ Rate limit hit. Waiting 245s before retrying...
```

No manual intervention needed — the pipeline resumes automatically after waiting the exact time Groq specifies.

**Token usage per run (approximate):**

| Agent | Tokens |
|---|---|
| BA + Architect + PM | ~1,500 |
| Dev Agent (8 tasks) | ~28,000 |
| QA Agent (8 reviews) | ~18,000 |
| **Total** | **~47,500** |

---

## 🐛 Known Issues & Fixes

| Issue | Fix Applied |
|---|---|
| Model decommissioned (429) | Updated to `llama-3.3-70b-versatile` |
| Infinite loop on Task 1 | Created dedicated `advance_task` node |
| QA too strict, hitting retry limit | Narrowed QA scope to syntax/import errors only |
| Rate limit crashes pipeline | Added `with_retry()` wrapper on all agents |
| Page resets while typing | Enforced `st.session_state` + `selectbox` navigation |
| View/Delete tasks missing | Hardcoded final PM task with all CRUD operations |
| Duplicate users in DB | Added `UNIQUE` constraint on username column |
| Reports page crash (date comparison) | Always compare string dates using `strftime` |
| `st.progress_bar()` not found | Enforced `st.progress()` with float 0.0–1.0 |
| Update task only works for first task | Enforced unique `key=f"widget_{{task_id}}"` per task |

---

## 🔮 Future Improvements

| Improvement |
|---|
| GitHub Push Agent — auto-commit and push generated code |
| Automated UAT Agent — Playwright agent tests the running app |
| LangGraph Checkpointing — resume interrupted runs from last node |
| Multi-file Generation — separate files per task, merge before QA |
| Human Review at Architecture stage — approve schema before Dev runs |
| Smart Token Management — auto-switch to 8B model near daily limit |
| Auto requirements.txt — scan generated app.py for imports |

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

Built with [LangGraph](https://github.com/langchain-ai/langgraph), [LangChain](https://github.com/langchain-ai/langchain), [Groq](https://groq.com), and [Streamlit](https://streamlit.io).
