import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# Heavy model — used for BA, Architect, PM, Dev (complex reasoning)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    api_key=os.getenv("GROQ_API_KEY")
)

# Light model — used for QA (simple pass/fail review, saves tokens)
llm_fast = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.1,
    api_key=os.getenv("GROQ_API_KEY")
)