"""
STEP 2 — api.py
================
What this does (simple):
  Wraps our ask.py logic into a REST API
  So anyone can call it via HTTP request

Endpoints:
  GET  /          → health check
  POST /ask       → ask a question, get answer with citations
  GET  /history   → see all past questions (stored in SQLite for now)

Run it:
  uvicorn api:app --reload --port 8000

Test it:
  Open browser → http://localhost:8000/docs  (auto Swagger UI!)
"""

import os
import sqlite3
import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from groq import Groq

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "privacy_docs"
TOP_K = 4
DB_FILE = "./query_logs.db"   # SQLite — simple local DB (no setup needed!)

# ──────────────────────────────────────────────
# SETUP: FastAPI app
# ──────────────────────────────────────────────

app = FastAPI(
    title="PrivacyGPT API",
    description="Ask questions about your privacy/policy documents",
    version="1.0.0"
)

# Allow frontend (React) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # In production: set your frontend URL here
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# SETUP: SQLite DB for logging queries
# SQLite = simplest DB, no installation needed
# We'll upgrade to PostgreSQL in Step 6 (Docker)
# ──────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS query_logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            question  TEXT NOT NULL,
            answer    TEXT NOT NULL,
            sources   TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def log_query(question: str, answer: str, sources: str):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO query_logs (question, answer, sources, timestamp) VALUES (?, ?, ?, ?)",
        (question, answer, sources, datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

# ──────────────────────────────────────────────
# SETUP: Load ChromaDB + Embeddings ONCE
# (not on every request — that would be slow!)
# ──────────────────────────────────────────────

print("🔢 Loading embedding model...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("🗄️  Loading ChromaDB...")
vectorstore = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings,
    collection_name=COLLECTION_NAME,
)

print("🤖 Setting up Groq client...")
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("❌ GROQ_API_KEY not set! Run: export GROQ_API_KEY='gsk_...'")
client = Groq(api_key=api_key)
# Init DB
init_db()
print("✅ PrivacyGPT API ready!\n")

# ──────────────────────────────────────────────
# REQUEST / RESPONSE MODELS
# Pydantic = validates input automatically
# ──────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str

    class Config:
        json_schema_extra = {
            "example": {"question": "How many sick leaves are allowed per year?"}
        }

class SourceItem(BaseModel):
    index: int
    page: int
    preview: str

class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceItem]
    timestamp: str

class HistoryItem(BaseModel):
    id: int
    question: str
    answer: str
    timestamp: str

# ──────────────────────────────────────────────
# CORE RAG FUNCTION (same logic as ask.py)
# ──────────────────────────────────────────────

def run_rag(question: str) -> tuple[str, list[SourceItem]]:
    # 1. Search ChromaDB
    results = vectorstore.similarity_search(question, k=TOP_K)

    if not results:
        return "I don't have enough information in the documents to answer this. Please contact the DPO.", []

    # 2. Build context
    context_parts = []
    for i, doc in enumerate(results, 1):
        page_num = doc.metadata.get("page", "?")
        context_parts.append(f"[{i}] (Page {page_num}):\n{doc.page_content}")
    context = "\n\n---\n\n".join(context_parts)

    # 3. Build sources list
    sources = []
    for i, doc in enumerate(results, 1):
        sources.append(SourceItem(
            index=i,
            page=doc.metadata.get("page", 0),
            preview=doc.page_content[:100].replace("\n", " ")
        ))

    # 4. Call Claude
    prompt = f"""You are PrivacyGPT, an assistant that answers questions about policy documents.

RULES:
- Answer ONLY using the context provided below.
- Every factual claim MUST have a citation like [1] or [2].
- If the answer is not in the context, say: "I don't have enough information in the documents to answer this."
- Be concise and clear.

CONTEXT:
{context}

QUESTION: {question}

ANSWER (with citations):"""

    response = client.chat.completions.create(
      model="llama-3.1-8b-instant",  # Fast and free on Groq
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    answer = response.choices[0].message.content
    return answer, sources

# ──────────────────────────────────────────────
# ROUTES (API Endpoints)
# ──────────────────────────────────────────────

@app.get("/")
def health_check():
    """Check if API is running"""
    return {
        "status": "✅ running",
        "app": "PrivacyGPT",
        "version": "1.0.0",
        "docs": "http://localhost:8000/docs"
    }


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """
    Ask a question about your policy documents.
    Returns answer with citations and source chunks.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if len(request.question) > 1000:
        raise HTTPException(status_code=400, detail="Question too long (max 1000 chars)")

    # Run RAG
    answer, sources = run_rag(request.question)

    # Log to SQLite
    sources_str = " | ".join([f"Page {s.page}: {s.preview}" for s in sources])
    log_query(request.question, answer, sources_str)

    return AskResponse(
        question=request.question,
        answer=answer,
        sources=sources,
        timestamp=datetime.datetime.now().isoformat()
    )


@app.get("/history", response_model=list[HistoryItem])
def get_history(limit: int = 10):
    """
    Get last N questions asked.
    Useful for DPO dashboard later.
    """
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute(
        "SELECT id, question, answer, timestamp FROM query_logs ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()

    return [
        HistoryItem(id=r[0], question=r[1], answer=r[2], timestamp=r[3])
        for r in rows
    ]