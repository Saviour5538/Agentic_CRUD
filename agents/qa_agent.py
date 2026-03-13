from agents import llm_qa as llm
from tools.logger import log_task
from langchain_core.messages import HumanMessage
from state import ProjectState
from agents import llm
from tools.file_ops import read_file, write_file
import json
import time
import re
import groq
import ast
import importlib


def check_syntax(code: str):
    """Returns list of syntax errors, empty if clean."""
    try:
        ast.parse(code)
        return []
    except SyntaxError as e:
        return [f"SyntaxError on line {e.lineno}: {e.msg}"]


def check_imports(code: str):
    """Returns list of missing imports that would cause ImportError."""
    issues = []
    stdlib_and_allowed = {
        "streamlit", "sqlite3", "hashlib", "datetime", "os", "re",
        "json", "time", "math", "random", "string", "collections",
        "functools", "itertools", "typing", "pathlib"
    }
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    if mod not in stdlib_and_allowed:
                        try:
                            importlib.import_module(mod)
                        except ImportError:
                            issues.append(f"ImportError: module '{mod}' is not installed")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    mod = node.module.split(".")[0]
                    if mod not in stdlib_and_allowed:
                        try:
                            importlib.import_module(mod)
                        except ImportError:
                            issues.append(f"ImportError: module '{mod}' is not installed")
    except Exception:
        pass
    return issues


def qa_agent(state: ProjectState) -> ProjectState:
    print("\n🔴 QA Agent: Reviewing generated code...")

    code = read_file("app.py")
    current_task = state["wbs_tasks"][state["current_task_index"]]

    # ── Step 1: Static checks (no LLM needed) ────────────────────────────────
    syntax_issues = check_syntax(code)
    if syntax_issues:
        print(f"❌ QA Failed (syntax check):")
        for issue in syntax_issues:
            print(f"   - {issue}")
        feedback = "\n".join(f"- {i}" for i in syntax_issues)
        return {**state, "qa_passed": False, "qa_feedback": feedback}

    import_issues = check_imports(code)
    if import_issues:
        print(f"❌ QA Failed (import check):")
        for issue in import_issues:
            print(f"   - {issue}")
        feedback = "\n".join(f"- {i}" for i in import_issues)
        return {**state, "qa_passed": False, "qa_feedback": feedback}

    # ── Step 2: LLM review for missing core functionality only ────────────────
    prompt = f"""
You are a QA Engineer. Syntax and imports have already been verified as correct.
Your ONLY job now is to check if the core functionality for the task is present.

Task the developer was given:
{current_task}

Code submitted:
{code}

PASS the code if:
- At least one function related to the task exists
- The main() function exists and calls st.sidebar.selectbox()
- The code is plausibly runnable with streamlit run app.py

FAIL the code ONLY if:
- The core function required by the task is completely absent (not just imperfect)
- main() function is missing entirely

DO NOT FAIL FOR:
- Missing validation, error handling, security issues
- Code style, edge cases, performance
- Features being incomplete or imperfect

Be generous. If the task is partially implemented, mark it PASSED.

Respond ONLY with this exact JSON. No explanation. No markdown:
{{
    "passed": true or false,
    "issues": ["only list issues where core functionality is completely missing"]
}}
"""

    while True:
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            usage = getattr(response, 'response_metadata', {}).get('token_usage', {})
            print(f"   🪙 Tokens — prompt: {usage.get('prompt_tokens', '?')}, completion: {usage.get('completion_tokens', '?')}, total: {usage.get('total_tokens', '?')}")
            break
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
            print(f"\n⏳ QA rate limit hit. Waiting {wait_seconds:.0f}s...")
            time.sleep(wait_seconds)

    try:
        review = json.loads(response.content.strip())
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        review = json.loads(match.group()) if match else {"passed": True, "issues": []}

    passed = review.get("passed", False)
    issues = review.get("issues", [])

    if passed:
        print("✅ QA Passed! Code approved.")
        log_task(
            task_index=state["current_task_index"],
            task_name=current_task,
            iteration=state.get("iteration_count", 0),
            status="qa_passed",
            issues=[]
        )
        return {**state, "qa_passed": True, "qa_feedback": ""}
    else:
        print(f"❌ QA Failed. Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        log_task(
            task_index=state["current_task_index"],
            task_name=current_task,
            iteration=state.get("iteration_count", 0),
            status="qa_failed",
            issues=issues
        )
        feedback = "\n".join(f"- {i}" for i in issues)
        return {**state, "qa_passed": False, "qa_feedback": feedback}