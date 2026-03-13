from agents import llm_architect as llm
from langchain_core.messages import HumanMessage
from state import ProjectState
from agents import llm_fast
from tools.file_ops import write_file
from tools.logger import log_stage
import re

def design_architecture(state: ProjectState) -> ProjectState:
    print("\n🟣 Architect Agent: Designing system architecture...")

    in_scope = "\n".join(f"- {item}" for item in state["sow"].get("in_scope", []))

    prompt = f"""
You are a Software Architect. Based on the SOW below, design the technical 
architecture for a Python CRUD application using Streamlit (UI) and SQLite (database).

In-Scope Features:
{in_scope}

Your response must include:
1. The SQLite database schema (table name, columns, data types) — be concise
2. A list of Python files needed and what each does — keep it brief
3. A Mermaid.js ER diagram of the database

IMPORTANT: Be concise. Do not over-explain. Short descriptions only.

Format your response exactly like this:

## Database Schema
<describe tables and columns clearly but briefly>

## File Structure
<list each file and its responsibility in one line each>

## Mermaid Diagram
```mermaid
erDiagram
    <your diagram here>
```
"""

    response = llm_fast.invoke([HumanMessage(content=prompt)])
    full_schema = response.content

    # Save full schema to file
    write_file("architecture.md", full_schema)

    # Extract Mermaid diagram
    mermaid_match = re.search(r'```mermaid(.*?)```', full_schema, re.DOTALL)
    mermaid_diagram = mermaid_match.group(1).strip() if mermaid_match else ""

    # Extract DB schema section
    db_schema_match = re.search(r'## Database Schema(.*?)## File Structure', full_schema, re.DOTALL)
    db_schema = db_schema_match.group(1).strip() if db_schema_match else ""

    # Extract file structure section
    file_structure_match = re.search(r'## File Structure(.*?)## Mermaid', full_schema, re.DOTALL)
    file_structure = file_structure_match.group(1).strip() if file_structure_match else ""

    # Trim Mermaid from what gets passed to Dev/PM
    trimmed_schema = re.sub(
        r'```mermaid.*?```',
        '[ER diagram removed to save tokens]',
        full_schema,
        flags=re.DOTALL
    ).strip()

    usage = getattr(response, 'response_metadata', {}).get('token_usage', {})

    log_stage("architect_agent", {
        "database_schema": db_schema,
        "file_structure": file_structure,
        "mermaid_diagram": mermaid_diagram,
        "mermaid_live_url": "https://mermaid.live — paste diagram there to visualise",
        "architecture_md": "generated_workspace/architecture.md",
        "tokens": {
            "prompt": usage.get("prompt_tokens"),
            "completion": usage.get("completion_tokens"),
            "total": usage.get("total_tokens")
        }
    })

    print(f"✅ Architecture designed.")
    print(f"   📄 Full architecture saved to generated_workspace/architecture.md")
    print(f"   📏 Schema — full: {len(full_schema)} chars, trimmed: {len(trimmed_schema)} chars")
    print(f"   🪙 Tokens — prompt: {usage.get('prompt_tokens', '?')}, completion: {usage.get('completion_tokens', '?')}, total: {usage.get('total_tokens', '?')}")

    return {**state, "architecture_schema": trimmed_schema}