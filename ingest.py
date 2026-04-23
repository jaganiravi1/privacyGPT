"""
STEP 1A — ingest.py
====================
What this does (simple):
  1. Reads your PDF file
  2. Cuts it into small chunks (like cutting a book into pages)
  3. Converts each chunk into numbers (embeddings) — FREE using HuggingFace
  4. Saves everything into ChromaDB (local database on your disk)

Run it:
  python ingest.py
"""

import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ──────────────────────────────────────────────
# CONFIG — change these to match your files
# ──────────────────────────────────────────────

PDF_PATH = "leave_policy.pdf"       # 👈 Put your PDF file name here
CHROMA_DIR = "./chroma_db"            # Where ChromaDB saves data on your disk
COLLECTION_NAME = "privacy_docs"      # Just a name for your document collection

# ──────────────────────────────────────────────
# STEP 1: Load the PDF
# ──────────────────────────────────────────────

print("📄 Loading PDF...")
loader = PyMuPDFLoader(PDF_PATH)
pages = loader.load()
print(f"   ✅ Loaded {len(pages)} pages from '{PDF_PATH}'")

# ──────────────────────────────────────────────
# STEP 2: Split into chunks
# Think of it like cutting a long article into
# small paragraphs so the AI can find answers easily
# ──────────────────────────────────────────────

print("\n✂️  Splitting into chunks...")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,        # Each chunk = ~500 characters (about 1 paragraph)
    chunk_overlap=50,      # 50 chars overlap so we don't lose context at edges
)
chunks = splitter.split_documents(pages)
print(f"   ✅ Created {len(chunks)} chunks from {len(pages)} pages")

# ──────────────────────────────────────────────
# STEP 3: Create embeddings (convert text → numbers)
# Using HuggingFace — 100% FREE, runs on your laptop
# First run downloads ~90MB model. After that it's instant.
# ──────────────────────────────────────────────

print("\n🔢 Loading embedding model (HuggingFace — free)...")
print("   ⏳ First time: downloads ~90MB model. Be patient...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"  # Small, fast, free model
)
print("   ✅ Embedding model ready!")

# ──────────────────────────────────────────────
# STEP 4: Store in ChromaDB (local vector database)
# This is like saving everything to a special
# searchable database on your disk
# ──────────────────────────────────────────────

print(f"\n🗄️  Saving to ChromaDB at '{CHROMA_DIR}'...")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=CHROMA_DIR,
    collection_name=COLLECTION_NAME,
)
print(f"   ✅ Saved {len(chunks)} chunks to ChromaDB!")

print("\n🎉 Done! Your PDF is now ready to be searched.")
print(f"   Database saved at: {os.path.abspath(CHROMA_DIR)}")
print("\n👉 Now run: python ask.py")
