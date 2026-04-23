# HRGPT — Beginner Setup Guide 🚀

Welcome to your local AI document assistant! This guide will show you exactly how to run the project from scratch. It reads your PDFs (like company leave policies) and answers questions based *only* on those rules using the super-fast Groq AI.

## What you need
- Python installed on your computer
- A PDF document (like an HR policy, employee handbook, etc.)
- A free **Groq API key** → Get it here: [console.groq.com/keys](https://console.groq.com/keys)

---

## The Exactly Step-by-Step Process

### 1. Open your terminal in this folder
Ensure your terminal (command prompt) is currently opened in the `privacygpt` folder.

### 2. Install required packages
You need some Python libraries to run AI locally. Run this command:
```bash
pip install -r requirements.txt
pip install groq
```
*(This may take 1-2 minutes the first time you run it.)*

### 3. Add your PDF Document
1. Find the PDF containing your company policies (e.g., leave policies).
2. Put the PDF into this exact same folder.
3. If it is named something else, **rename it to `privacy_policy.pdf`** so the script knows where to find it. *(Alternatively, edit `ingest.py` to match your exact file name).*

### 4. Create the Database (Ingestion)
Now we need to make the AI "read" your PDF and slice it up into a tiny local database.

Run this:
```bash
python3 ingest.py
```
✅ You'll see: "Saved X chunks to ChromaDB!"
*(If you change your PDF later, just run this command again to update the database!)*

### 5. Set up your AI Brain (Groq API)
The script needs permission to talk to Groq. In your terminal, run the following to securely load your API key:

**Mac/Linux:**
```bash
export GROQ_API_KEY="gsk_your_key_here"
```

**Windows CMD:**
```bash
set GROQ_API_KEY=gsk_your_key_here
```

**Windows PowerShell:**
```bash
$env:GROQ_API_KEY="gsk_your_key_here"
```

### 6. Ask Questions!
Everything is ready! Start the chat interface by running:
```bash
python3 ask.py
```

Then literally type any question like:
- "Can I take 20 days continuous leave as paid?"
- "What is the policy for sick leave?"
- "Who do I contact for payroll issues?"

*(Type `quit` to exit at any time).*

---

## 💸 Cost & Privacy Notes
- **Reading the PDF:** 100% FREE. It runs locally on your computer.
- **Database:** 100% FREE. It's saved in a new folder called `chroma_db` right next to your files.
- **Chatting:** 100% FREE. We are using Groq's fast tier which is completely free for personal use!

---

## 🚨 Common Beginner Errors

**Error: GROQ_API_KEY not set! / NameError / Authentication Error**
→ You forgot Step 5. Go to console.groq.com/keys, copy your key, and run the `export GROQ_API_KEY=...` command again. You have to do this once every time you open a brand new terminal window.

**Error: Model decommissioned (llama3-8b-8192)**
→ Update line 112 in `ask.py` to say `model="llama-3.1-8b-instant",`. (This is already fixed!).

**Error: PDF not found**
→ Make sure `privacy_policy.pdf` is in the SAME folder as `ingest.py`, and is spelled perfectly in lowercase.