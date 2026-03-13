from agents import llm_pm as llm
from langchain_core.messages import HumanMessage
from state import ProjectState
from agents import llm_fast
from tools.logger import log_stage
import json

def create_wbs(state: ProjectState) -> ProjectState:
    print("\n🟡 PM Agent: Creating Work Breakdown Structure...")

    in_scope = "\n".join(f"- {item}" for item in state["sow"].get("in_scope", []))

    prompt = f"""
You are a Project Manager. Based on the SOW and architecture below, break the 
development into a list of small, ordered coding tasks for a developer.

SOW In-Scope Features:
{in_scope}

Architecture:
{state['architecture_schema']}

STRICT RULES:
- Every single feature listed in the SOW In-Scope MUST have at least one task
- Tasks must be ordered by dependency (DB first, then logic, then UI)
- The final task must ALWAYS be: "Build the complete Streamlit app.py with 
  ALL CRUD operations: Register, Login, View Tasks, Create Task, Update Task, 
  Delete Task with confirmation, and Reports"
- You MUST return between 6 and 8 tasks. No more than 8. No less than 6.
- If you have more than 8 tasks, combine related ones into a single task

Respond ONLY with a valid JSON array of strings.
No explanation. No markdown. Just the raw JSON array.
"""

    response = llm_fast.invoke([HumanMessage(content=prompt)])

    try:
        tasks = json.loads(response.content.strip())
    except json.JSONDecodeError:
        import re
        match = re.search(r'\[.*\]', response.content, re.DOTALL)
        tasks = json.loads(match.group()) if match else ["Task 1: Build the full CRUD app in app.py"]
    
    # Hard cap at 8 tasks regardless of what model returns
    if len(tasks) > 8:
        print(f"   ⚠️  PM returned {len(tasks)} tasks, trimming to 8...")
        # Always keep the last task (hardcoded final task)
        tasks = tasks[:7] + [tasks[-1]]

    usage = getattr(response, 'response_metadata', {}).get('token_usage', {})

    log_stage("pm_agent", {
        "total_tasks": len(tasks),
        "tasks": tasks,
        "tokens": {
            "prompt": usage.get("prompt_tokens"),
            "completion": usage.get("completion_tokens"),
            "total": usage.get("total_tokens")
        }
    })

    print(f"✅ WBS Created: {len(tasks)} tasks")
    for i, t in enumerate(tasks):
        print(f"   {i+1}. {t}")
    print(f"   🪙 Tokens — prompt: {usage.get('prompt_tokens', '?')}, completion: {usage.get('completion_tokens', '?')}, total: {usage.get('total_tokens', '?')}")

    return {**state, "wbs_tasks": tasks, "current_task_index": 0}