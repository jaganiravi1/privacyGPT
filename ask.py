"""
STEP 1B — ask.py
=================
What this does (simple):
  1. Takes your question
  2. Searches ChromaDB for the most relevant chunks
  3. Sends those chunks + your question to Claude API
  4. Claude answers with citations [1][2] from your actual document

Run it:
  python ask.py

You need:
  - ANTHROPIC_API_KEY set (free $5 credits on signup at console.anthropic.com)
  - ChromaDB already populated (run ingest.py first!)
"""

import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from groq import Groq

# ──────────────────────────────────────────────
# CONFIG — must match what you used in ingest.py
# ──────────────────────────────────────────────

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "privacy_docs"
TOP_K = 4  # How many chunks to retrieve per question (4 is a good start)

# ──────────────────────────────────────────────
# SETUP: API key check
# Get your free key at: https://console.anthropic.com
# Then run: export ANTHROPIC_API_KEY="sk-ant-..."
# ──────────────────────────────────────────────

api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    print("❌ ERROR: GROQ_API_KEY not set!")
    print("   1. Go to https://console.groq.com/keys → get your free API key")
    print("   2. Run: export GROQ_API_KEY='gsk_...'")
    print("   3. Then run this script again")
    exit(1)

# ──────────────────────────────────────────────
# LOAD: ChromaDB + Embeddings
# ──────────────────────────────────────────────

print("🗄️  Loading ChromaDB...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
vectorstore = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings,
    collection_name=COLLECTION_NAME,
)
print("   ✅ ChromaDB loaded!")

# ──────────────────────────────────────────────
# CLAUDE CLIENT
# Using claude-haiku — fastest & cheapest model
# Perfect for learning. Costs ~$0.001 per question
# ──────────────────────────────────────────────

client = Groq(api_key=api_key)

# ──────────────────────────────────────────────
# THE MAIN FUNCTION: Ask a question
# ──────────────────────────────────────────────

def ask(question: str) -> str:
    """
    Flow:
      question → search DB → get chunks → send to Claude → get answer with citations
    """

    # 1. Search ChromaDB for relevant chunks
    results = vectorstore.similarity_search(question, k=TOP_K)

    if not results:
        return "❌ No relevant content found in the documents. Try a different question."

    # 2. Build context string with chunk numbers
    #    This is what we send to Claude alongside the question
    context_parts = []
    for i, doc in enumerate(results, 1):
        page_num = doc.metadata.get("page", "?")
        context_parts.append(f"[{i}] (Page {page_num}):\n{doc.page_content}")

    context = "\n\n---\n\n".join(context_parts)

    # 3. Build the prompt
    #    We tell Claude: only use the context below, always cite with [1][2]
    prompt = f"""
You are PrivacyGPT...

RULES:
- Answer ONLY using the context
- Keep answers practical and direct
- Use natural human language (not robotic)
- If contact info exists → include it clearly
- Only cite if needed

- If NOT found:
Say:
"I couldn't find this in the documents. Please contact HR at hr@zignuts.com"
DO NOT add citations.

CONTEXT:
{context}

QUESTION: {question}
"""

    # 4. Call Groq API
    response = client.chat.completions.create(
       model="llama3-8b-8192",  # Fast and free on Groq
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    answer = response.choices[0].message.content

    # 5. Show sources used
    sources_used = "\n\nSources used:"
    for i, doc in enumerate(results, 1):
        page_num = doc.metadata.get("page", "?")
        preview = doc.page_content[:80].replace("\n", " ")
        sources_used += f"\n  [{i}] Page {page_num} — \"{preview}...\""

    return answer + sources_used


# ──────────────────────────────────────────────
# INTERACTIVE LOOP
# Just keeps asking until you type 'quit'
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  🤖 PrivacyGPT — Step 1 (Local RAG Demo)")
    print("  Type your question. Type 'quit' to exit.")
    print("="*55 + "\n")

    while True:
        question = input("You: ").strip()

        if not question:
            continue

        if question.lower() in ("quit", "exit", "q"):
            print("👋 Bye!")
            break

        print("\n⏳ Searching documents and asking Groq...\n")
        answer = ask(question)
        print(f"PrivacyGPT: {answer}")
        print("\n" + "-"*55 + "\n")