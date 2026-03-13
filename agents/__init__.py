import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# BA Agent — simple JSON, fast and token efficient
llm_ba = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.3,
    api_key=os.getenv("GROQ_API_KEY")
)

# agents/__init__.py — update Architect model
llm_architect = ChatGroq(
    model="moonshotai/kimi-k2-instruct",
    temperature=0.2,
    api_key=os.getenv("GROQ_API_KEY")
)

# PM Agent — switch to llama-3.1-8b-instant
llm_pm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2,
    api_key=os.getenv("GROQ_API_KEY")
)

# Dev Agent — best model for code generation
llm_dev = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    api_key=os.getenv("GROQ_API_KEY")
)

# QA Agent — switched to llama-4-scout (separate token pool)
llm_qa = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0.1,
    api_key=os.getenv("GROQ_API_KEY")
)

# Backward compatibility
llm = llm_dev
llm_fast = llm_ba