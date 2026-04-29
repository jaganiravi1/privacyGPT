# PrivacyGPT — Beginner Setup Guide 🚀

Welcome to **PrivacyGPT** — your local AI-powered policy assistant with Slack integration! This guide will show you exactly how to run the project from scratch. It reads your PDFs (like company leave policies) and answers questions based *only* on those documents using the super-fast Groq AI — directly inside Slack.

## What You Need
- Python 3.10+ installed on your computer
- A PDF document (like an HR policy, leave policy, etc.)
- A free **Groq API key** → [console.groq.com/keys](https://console.groq.com/keys)
- A free **Slack workspace** → [slack.com](https://slack.com) *(for Slack bot only)*
- A free **Cloudflare Tunnel** → `brew install cloudflare/cloudflare/cloudflared` *(for Slack bot only)*

---

## 📁 Project Structure

```
privacygpt/
├── ingest.py         → Load PDF into ChromaDB (run once)
├── ask.py            → Ask questions via terminal (CLI)
├── api.py            → FastAPI REST API (/ask, /history)
├── slack_bot.py      → Slack /ask command bot
├── requirements.txt  → All dependencies
├── chroma_db/        → Auto-created after running ingest.py
└── query_logs.db     → Auto-created after running api.py
```

---

## ⚙️ Step-by-Step Setup

### Step 1 — Open Terminal in This Folder
Make sure your terminal is opened inside the `privacygpt` folder:
```bash
cd /path/to/privacygpt
```

---

### Step 2 — Install Required Packages
```bash
pip install -r requirements.txt
pip install groq
```
*(Takes 2–3 minutes the first time. Downloads ~90MB embedding model.)*

---

### Step 3 — Add Your PDF
1. Put your PDF file inside this folder
2. Open `ingest.py` and update line 20:
```python
PDF_PATH = "leave_policy.pdf"   # 👈 change to your actual filename
```

---

### Step 4 — Create the Database (Ingestion)
This makes the AI "read" your PDF and store it in a local searchable database:
```bash
python3 ingest.py
```
✅ You should see:
```
📄 Loading PDF...
   ✅ Loaded X pages
✂️  Splitting into chunks...
   ✅ Created X chunks
🗄️  Saving to ChromaDB...
   ✅ Saved X chunks to ChromaDB!
🎉 Done!
```
*(If you update your PDF later, just run this again!)*

---

### Step 5 — Set Your Groq API Key

**Mac/Linux:**
```bash
export GROQ_API_KEY="gsk_your_key_here"
```

**Windows CMD:**
```
set GROQ_API_KEY=gsk_your_key_here
```

**Windows PowerShell:**
```
$env:GROQ_API_KEY="gsk_your_key_here"
```

> 💡 **Tip:** Add this to `~/.zshrc` or `~/.bashrc` so you don't have to do it every time:
> ```bash
> echo 'export GROQ_API_KEY="gsk_your_key_here"' >> ~/.zshrc
> source ~/.zshrc
> ```

---

## 🖥️ Option A — Ask via Terminal (Quickest)

```bash
python3 ask.py
```

Then type any question:
```
You: How many sick leaves do I get per year?
You: Can I carry forward unused leaves?
You: Who do I contact for payroll issues?
```
*(Type `quit` to exit)*

---

## ⚡ Option B — Run the REST API

Start the FastAPI server:
```bash
uvicorn api:app --reload --port 8000
```

Then open your browser:
```
http://localhost:8000/docs     ← Swagger UI (test here!)
http://localhost:8000/         ← Health check
http://localhost:8000/history  ← Past questions log
```

Or call it via terminal:
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How many leaves do I get?"}'
```

---

## 💬 Option C — Run the Slack Bot

### One-Time Slack App Setup
1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From Scratch**
2. App Name: `PrivacyGPT` | Select your workspace
3. Go to **Slash Commands** → Create `/ask` command
4. Go to **OAuth & Permissions** → Add scopes: `chat:write`, `commands`
5. Click **Install to Workspace** → Copy **Bot User OAuth Token** (`xoxb-...`)
6. Go to **Basic Information** → Copy **Signing Secret**

### Set Slack Environment Variables
```bash
export SLACK_BOT_TOKEN="xoxb_your_token_here"
export SLACK_SIGNING_SECRET="your_signing_secret_here"
export GROQ_API_KEY="gsk_your_key_here"
```

### Terminal 1 — Start the Bot
```bash
python3 slack_bot.py
```

### Terminal 2 — Start Cloudflare Tunnel
```bash
cloudflared tunnel --url http://localhost:3000
```
Copy the URL it gives you → example: `https://abc-xyz.trycloudflare.com`

### Update Slack Dashboard
Go to [api.slack.com/apps](https://api.slack.com/apps) → Your App → **Slash Commands** → `/ask` → **Edit**:
```
Request URL: https://abc-xyz.trycloudflare.com/slack/ask
```
Save ✅

### Test in Slack
```
/ask How many sick leaves do I get?
/ask What is the carry forward policy?
/ask How do I apply for leave?
```

> ⚠️ **Note:** Cloudflare tunnel URL changes every time you restart. Update the Slack Request URL each time.

---

## 💸 Cost & Privacy

| Component | Cost | Where it runs |
|-----------|------|---------------|
| PDF Reading (PyMuPDF) | FREE | Your laptop |
| Embeddings (HuggingFace) | FREE | Your laptop |
| ChromaDB (vector database) | FREE | Your laptop |
| Groq LLaMA AI | FREE tier | Groq cloud |
| Slack Bot | FREE | Slack free plan |
| Cloudflare Tunnel | FREE | Cloudflare |

**Total cost: ₹0** 🎉

---

## 🚨 Common Errors & Fixes

**Error: `GROQ_API_KEY not set`**
→ Run `export GROQ_API_KEY="gsk_your_key"` again. Must be done every new terminal session unless added to `~/.zshrc`.

**Error: `Model not found: llama3-8b-8192`**
→ Update model name to `llama-3.1-8b-instant` in `ask.py` and `api.py`.

**Error: `PDF not found`**
→ Make sure PDF filename in `ingest.py` exactly matches your file. Check spelling and lowercase.

**Error: `No module named langchain_huggingface`**
→ Run: `pip install langchain-huggingface langchain-chroma`

**Error: `ssl.SSLCertVerificationError` (Mac)**
→ Run: `/Applications/Python\ 3.14/Install\ Certificates.command`

**Slack: `dispatch_failed` or no response**
→ Cloudflare tunnel URL has changed. Restart tunnel → copy new URL → update Slack Request URL.

**Slack: `500 Internal Server Error`**
→ Check terminal running `slack_bot.py` for error details. Usually means API key is not set.

---

## 🔗 Useful Links

| Resource | Link |
|----------|------|
| GitHub Repo | [github.com/jaganiravi1/privacyGPT](https://github.com/jaganiravi1/privacyGPT) |
| Groq API Keys | [console.groq.com/keys](https://console.groq.com/keys) |
| Slack App Dashboard | [api.slack.com/apps](https://api.slack.com/apps) |
| Cloudflare Tunnel Docs | [developers.cloudflare.com/cloudflare-one/connections/connect-networks](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks) |
| FastAPI Docs | [fastapi.tiangolo.com](https://fastapi.tiangolo.com) |

---

```
✅ Phase 1 — RAG Pipeline (PDF → ChromaDB)
✅ Phase 2 — FastAPI REST API
✅ Phase 3 — Slack Bot (/ask command)
```