from agents import llm_ba as llm
from langchain_core.messages import HumanMessage
from state import ProjectState
from agents import llm_fast
from tools.logger import log_stage
import json

def generate_sow(state: ProjectState) -> ProjectState:
    print("\n🔵 BA Agent: Generating Statement of Work...")

    prompt = f"""
You are a Business Analyst. Based on the problem statement below, generate a detailed 
Statement of Work (SOW) for a CRUD application.

Problem Statement: {state['problem_statement']}

Respond ONLY with a valid JSON object in this exact format:
{{
    "in_scope": ["list of features that WILL be built"],
    "out_scope": ["list of features that will NOT be built"]
}}

No explanation. No markdown. Just the raw JSON.
"""

    response = llm_fast.invoke([HumanMessage(content=prompt)])

    try:
        sow = json.loads(response.content.strip())
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        sow = json.loads(match.group()) if match else {"in_scope": [], "out_scope": []}

    usage = getattr(response, 'response_metadata', {}).get('token_usage', {})

    log_stage("ba_agent", {
        "in_scope": sow.get("in_scope", []),
        "out_scope": sow.get("out_scope", []),
        "tokens": {
            "prompt": usage.get("prompt_tokens"),
            "completion": usage.get("completion_tokens"),
            "total": usage.get("total_tokens")
        }
    })

    print(f"✅ SOW Generated:")
    print(f"   In Scope: {sow.get('in_scope')}")
    print(f"   Out Scope: {sow.get('out_scope')}")
    print(f"   🪙 Tokens — prompt: {usage.get('prompt_tokens', '?')}, completion: {usage.get('completion_tokens', '?')}, total: {usage.get('total_tokens', '?')}")

    return {**state, "sow": sow}