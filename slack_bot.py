"""
STEP 3 — slack_bot.py
======================
What this does:
  User types /ask How many leaves? in Slack
  → Bot searches ChromaDB
  → Bot asks Groq LLM
  → Bot replies with answer + citations in Slack

Run it:
  1. Start ngrok:     ngrok http 3000
  2. Update Request URL in Slack App dashboard
  3. Run bot:         python3 slack_bot.py
"""

import os
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from groq import Groq

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

CHROMA_DIR    = "./chroma_db"
COLLECTION    = "privacy_docs"
TOP_K         = 4

# ──────────────────────────────────────────────
# ENV KEYS — set these in terminal before running
# export SLACK_BOT_TOKEN="xoxb-..."
# export SLACK_SIGNING_SECRET="..."
# export GROQ_API_KEY="gsk_..."
# ──────────────────────────────────────────────

SLACK_BOT_TOKEN      = os.environ.get("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
GROQ_API_KEY         = os.environ.get("GROQ_API_KEY")

# Validate keys
missing = []
if not SLACK_BOT_TOKEN:      missing.append("SLACK_BOT_TOKEN")
if not SLACK_SIGNING_SECRET: missing.append("SLACK_SIGNING_SECRET")
if not GROQ_API_KEY:         missing.append("GROQ_API_KEY")

if missing:
    print(f"❌ Missing env vars: {', '.join(missing)}")
    print("Run these commands first:")
    for m in missing:
        print(f'  export {m}="your-value-here"')
    exit(1)

# ──────────────────────────────────────────────
# LOAD: Embeddings + ChromaDB (once at startup)
# ──────────────────────────────────────────────

print("🔢 Loading embedding model...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("🗄️  Loading ChromaDB...")
vectorstore = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings,
    collection_name=COLLECTION,
)

print("🤖 Setting up Groq client...")
groq_client = Groq(api_key=GROQ_API_KEY)

print("✅ All loaded!\n")

# ──────────────────────────────────────────────
# CORE RAG FUNCTION
# ──────────────────────────────────────────────

def run_rag(question: str) -> str:
    # 1. Search ChromaDB
    results = vectorstore.similarity_search(question, k=TOP_K)

    if not results:
        return "❌ I couldn't find relevant information. Please contact HR directly."

    # 2. Build context
    context_parts = []
    for i, doc in enumerate(results, 1):
        page = doc.metadata.get("page", "?")
        context_parts.append(f"[{i}] (Page {page}):\n{doc.page_content}")
    context = "\n\n---\n\n".join(context_parts)

    # 3. Prompt
    prompt = f"""You are PrivacyGPT, a helpful HR policy assistant on Slack.

RULES:
- Answer ONLY using the context below
- Be concise — this is a Slack message, not an essay
- Use simple language, no legal jargon
- Add citation numbers like [1] or [2] for facts
- If not found: say "I couldn't find this. Contact HR at hr@company.com"
- Format nicely for Slack (use *bold* for key points)

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

    # 4. Call Groq
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        max_tokens=500,   # Keep Slack replies short
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response.choices[0].message.content

    # 5. Add sources footer
    sources = "\n\n📄 *Sources:*"
    for i, doc in enumerate(results[:2], 1):  # Show top 2 sources only
        page = doc.metadata.get("page", "?")
        preview = doc.page_content[:60].replace("\n", " ")
        sources += f"\n[{i}] Page {page} — _{preview}..._"

    return answer + sources

# ──────────────────────────────────────────────
# SLACK APP SETUP
# ──────────────────────────────────────────────

slack_app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET
)

# ──────────────────────────────────────────────
# SLASH COMMAND HANDLER
# This runs when someone types /ask in Slack
# ──────────────────────────────────────────────

@slack_app.command("/ask")
def handle_ask(ack, respond, command):
    # 1. Acknowledge Slack immediately (required within 3 seconds!)
    ack()

    question = command.get("text", "").strip()

    # 2. Validate input
    if not question:
        respond("❓ Please provide a question!\nExample: `/ask How many sick leaves do I get?`")
        return

    # 3. Show typing indicator
    respond(f"🔍 Searching policy documents for: *{question}*\n_Please wait..._")

    # 4. Run RAG
    answer = run_rag(question)

    # 5. Send final answer
    respond({
        "response_type": "in_channel",   # visible to everyone in channel
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🤖 PrivacyGPT Answer"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Question:* {question}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": answer
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "⚡ Powered by PrivacyGPT · Groq LLaMA · ChromaDB"
                    }
                ]
            }
        ]
    })

# ──────────────────────────────────────────────
# FLASK SERVER (wraps Slack Bolt)
# ──────────────────────────────────────────────

flask_app = Flask(__name__)
handler = SlackRequestHandler(slack_app)

@flask_app.route("/slack/ask", methods=["POST"])
def slack_events():
    return handler.handle(request)

@flask_app.route("/", methods=["GET"])
def health():
    return {"status": "✅ PrivacyGPT Slack Bot running!"}

# ──────────────────────────────────────────────
# START SERVER
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("="*50)
    print("  🤖 PrivacyGPT Slack Bot")
    print("  Listening on http://localhost:3000")
    print("="*50)
    print("\n📋 Next steps:")
    print("  1. Open NEW terminal → run: ngrok http 3000")
    print("  2. Copy ngrok URL (e.g. https://abc123.ngrok.io)")
    print("  3. Go to api.slack.com → Your App → Slash Commands")
    print("  4. Update Request URL to: https://abc123.ngrok.io/slack/ask")
    print("  5. Go to Slack → type: /ask How many leaves do I get?\n")

    flask_app.run(port=3000, debug=False)
