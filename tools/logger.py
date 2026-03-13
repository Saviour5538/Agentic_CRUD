import json
import os
import datetime

LOG_FILE = "generated_workspace/pipeline_log.json"

def init_log(problem_statement: str):
    """Called once at the start of each pipeline run."""
    os.makedirs("generated_workspace", exist_ok=True)
    log = {
        "run_started_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "problem_statement": problem_statement,
        "stages": {}
    }
    _write(log)

def log_stage(stage: str, data: dict):
    """Called after each agent completes. Adds stage output to the log."""
    log = _read()
    log["stages"][stage] = {
        "completed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **data
    }
    _write(log)

def log_task(task_index: int, task_name: str, iteration: int, status: str, issues: list = None):
    """Called after each Dev/QA cycle."""
    log = _read()
    if "dev_qa_cycles" not in log:
        log["dev_qa_cycles"] = []
    log["dev_qa_cycles"].append({
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "task_index": task_index + 1,
        "task_name": task_name,
        "iteration": iteration,
        "status": status,
        "issues": issues or []
    })
    _write(log)

def finalize_log(total_tokens: int = None):
    """Called at the end of the pipeline run."""
    log = _read()
    log["run_completed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if total_tokens:
        log["total_tokens_used"] = total_tokens
    _write(log)
    print(f"\n📋 Full pipeline log saved to generated_workspace/pipeline_log.json")

def _read():
    if not os.path.exists(LOG_FILE):
        return {}
    with open(LOG_FILE, "r") as f:
        return json.load(f)

def _write(data: dict):
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)