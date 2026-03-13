from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from state import ProjectState
from agents.ba_agent import generate_sow
from agents.architect_agent import design_architecture
from agents.pm_agent import create_wbs
from agents.dev_agent import dev_agent
from agents.qa_agent import qa_agent
from tools.logger import init_log, finalize_log
import time
import re
import groq

load_dotenv()

# ── Retry wrapper ────────────────────────────────────────────────────────────

def with_retry(fn, state: ProjectState, max_wait: int = 300) -> ProjectState:
    while True:
        try:
            return fn(state)
        except groq.RateLimitError as e:
            wait_seconds = 60
            try:
                match = re.search(r'try again in (\d+)m([\d.]+)s', str(e))
                if match:
                    wait_seconds = int(match.group(1)) * 60 + float(match.group(2)) + 5
                else:
                    match = re.search(r'try again in ([\d.]+)s', str(e))
                    if match:
                        wait_seconds = float(match.group(1)) + 5
            except Exception:
                pass
            wait_seconds = min(wait_seconds, max_wait)
            print(f"\n⏳ Rate limit hit. Waiting {wait_seconds:.0f}s before retrying...")
            time.sleep(wait_seconds)

# ── Protected agent wrappers ─────────────────────────────────────────────────

def safe_ba(state: ProjectState) -> ProjectState:
    return with_retry(generate_sow, state)

def safe_architect(state: ProjectState) -> ProjectState:
    return with_retry(design_architecture, state)

def safe_pm(state: ProjectState) -> ProjectState:
    return with_retry(create_wbs, state)

def safe_dev(state: ProjectState) -> ProjectState:
    time.sleep(2)
    return with_retry(dev_agent, state)

def safe_qa(state: ProjectState) -> ProjectState:
    time.sleep(2)
    return with_retry(qa_agent, state)

# ── Routing & logic nodes ────────────────────────────────────────────────────

def route_qa(state: ProjectState):
    if not state.get("qa_passed"):
        if state.get("iteration_count", 0) >= 3:
            print(f"⚠️  Max retries hit on task {state['current_task_index'] + 1}, forcing next task...")
            return "advance_task"
        return "dev_agent"

    next_index = state["current_task_index"] + 1
    if next_index < len(state["wbs_tasks"]):
        return "advance_task"
    return "uat_human_approval"

def advance_task(state: ProjectState) -> ProjectState:
    next_index = state["current_task_index"] + 1
    print(f"\n➡️  Advancing to Task {next_index + 1}/{len(state['wbs_tasks'])}")
    return {
        **state,
        "current_task_index": next_index,
        "iteration_count": 0,
        "qa_feedback": "",
        "qa_passed": False,
    }

def uat_human_approval(state: ProjectState) -> ProjectState:
    print("\n✅ All tasks complete! Review generated_workspace/app.py")
    finalize_log()
    return {**state, "ready_for_uat": True}

# ── Graph definition ─────────────────────────────────────────────────────────

workflow = StateGraph(ProjectState)

workflow.add_node("generate_sow", safe_ba)
workflow.add_node("design_architecture", safe_architect)
workflow.add_node("create_wbs", safe_pm)
workflow.add_node("dev_agent", safe_dev)
workflow.add_node("qa_agent", safe_qa)
workflow.add_node("advance_task", advance_task)
workflow.add_node("uat_human_approval", uat_human_approval)

workflow.set_entry_point("generate_sow")
workflow.add_edge("generate_sow", "design_architecture")
workflow.add_edge("design_architecture", "create_wbs")
workflow.add_edge("create_wbs", "dev_agent")
workflow.add_edge("dev_agent", "qa_agent")
workflow.add_edge("advance_task", "dev_agent")

workflow.add_conditional_edges(
    "qa_agent",
    route_qa,
    {
        "dev_agent": "dev_agent",
        "advance_task": "advance_task",
        "uat_human_approval": "uat_human_approval"
    }
)

workflow.add_edge("uat_human_approval", END)

app = workflow.compile()

# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    initial_state: ProjectState = {
        "problem_statement": "Build a basic Task Management CRUD app",
        "sow": {},
        "architecture_schema": "",
        "wbs_tasks": [],
        "current_task_index": 0,
        "code_files": {},
        "qa_feedback": "",
        "qa_passed": False,
        "ready_for_uat": False,
        "iteration_count": 0,
    }

    # ── Init log before pipeline starts ──────────────────────────────────────
    init_log(initial_state["problem_statement"])

    result = app.invoke(initial_state)
    print("\n🏁 Pipeline finished.")