# PrivacyGPT — Beginner Setup Guide 🚀

Welcome to **PrivacyGPT** — your local AI-powered policy assistant with Slack integration! This guide will show you exactly how to run the project from scratch. It reads your PDFs (like company leave policies) and answers questions based *only* on those documents using the super-fast Groq AI — directly inside Slack.

## What You Need
- Python 3.10+ installed on your computer
- One or more PDF documents (like HR policy, leave policy, etc.) — place them in the `resources/` folder
- A free **Groq API key** → [console.groq.com/keys](https://console.groq.com/keys)
- A free **Slack workspace** → [slack.com](https://slack.com) *(for Slack bot only)*
- A free **Cloudflare Tunnel** → `brew install cloudflare/cloudflare/cloudflared` *(for Slack bot only)*

---

## 📁 Project Structure

```
privacygpt/
├── resources/        → 📂 Put ALL your PDF files here
├── ingest.py         → Load all PDFs from resources/ into ChromaDB (run once)
├── ask.py            → Ask questions via terminal (CLI)
├── api.py            → FastAPI REST API (/ask, /history)
├── slack_bot.py      → Slack /ask command bot
├── .env              → 🔐 Store all your API keys here (never share this file!)
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
pip install groq python-dotenv
```
*(Takes 2–3 minutes the first time. Downloads ~90MB embedding model.)*

---

### Step 3 — Add Your PDFs to the `resources/` Folder
1. Create a folder called `resources` inside the project (if not already there):
```bash
mkdir resources
```
2. Copy **all your PDF files** into it:
```
privacygpt/
└── resources/
    ├── leave_policy.pdf
    ├── hr_handbook.pdf
    ├── payroll_policy.pdf
    └── ...any other PDFs
```
3. `ingest.py` will automatically read **all PDFs** from this folder — no need to change any filenames in the code!

---

### Step 4 — Set Up Your `.env` File

1. Create a file named `.env` in the root of the project:
```bash
touch .env
```
2. Open it and add your keys like this:
```
GROQ_API_KEY=gsk_your_key_here
SLACK_BOT_TOKEN=xoxb_your_token_here
SLACK_SIGNING_SECRET=your_signing_secret_here
```
> ⚠️ **Never share or upload your `.env` file!** Add it to `.gitignore` immediately:
> ```bash
> echo ".env" >> .gitignore
> ```

> 💡 All scripts (`ask.py`, `api.py`, `slack_bot.py`) will automatically read keys from `.env` using `python-dotenv`. No more `export` commands every session!

---

### Step 5 — Create the Database (Ingestion)
This makes the AI "read" all PDFs in your `resources/` folder and store them in a local searchable database:
```bash
python3 ingest.py
```
✅ You should see:
```
📂 Found X PDF(s) in resources/
📄 Loading leave_policy.pdf...
   ✅ Loaded X pages
📄 Loading hr_handbook.pdf...
   ✅ Loaded X pages
✂️  Splitting into chunks...
   ✅ Created X chunks total
🗄️  Saving to ChromaDB...
   ✅ Saved X chunks to ChromaDB!
🎉 Done!
```
*(Added a new PDF to `resources/`? Just run `python3 ingest.py` again!)*

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
7. Paste both into your `.env` file (see Step 4)

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
→ Make sure `.env` file exists and has `GROQ_API_KEY=gsk_your_key`. Also check that `python-dotenv` is installed.

**Error: `resources/ folder not found`**
→ Create the folder: `mkdir resources` and put your PDFs inside it.

**Error: `No PDFs found in resources/`**
→ Make sure your files end in `.pdf` (lowercase) and are placed directly inside the `resources/` folder.

**Error: `Model not found: llama3-8b-8192`**
→ Update model name to `llama-3.1-8b-instant` in `ask.py` and `api.py`.

**Error: `No module named langchain_huggingface`**
→ Run: `pip install langchain-huggingface langchain-chroma`

**Error: `No module named dotenv`**
→ Run: `pip install python-dotenv`

**Error: `ssl.SSLCertVerificationError` (Mac)**
→ Run: `/Applications/Python\ 3.14/Install\ Certificates.command`

**Slack: `dispatch_failed` or no response**
→ Cloudflare tunnel URL has changed. Restart tunnel → copy new URL → update Slack Request URL.

**Slack: `500 Internal Server Error`**
→ Check that `.env` file has all 3 keys set correctly. Check terminal running `slack_bot.py` for details.

---

## 🔗 Useful Links

| Resource | Link |
|----------|------|
| GitHub Repo | [github.com/jaganiravi1/privacyGPT](https://github.com/jaganiravi1/privacyGPT) |
| Groq API Keys | [console.groq.com/keys](https://console.groq.com/keys) |
| Slack App Dashboard | [api.slack.com/apps](https://api.slack.com/apps) |
| Cloudflare Tunnel Docs | [developers.cloudflare.com/cloudflare-one/connections/connect-networks](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks) |
| FastAPI Docs | [fastapi.tiangolo.com](https://fastapi.tiangolo.com) |
| python-dotenv Docs | [pypi.org/project/python-dotenv](https://pypi.org/project/python-dotenv) |

---

```
✅ Phase 1 — RAG Pipeline (PDFs in resources/ → ChromaDB)
✅ Phase 2 — FastAPI REST API
✅ Phase 3 — Slack Bot (/ask command)
```