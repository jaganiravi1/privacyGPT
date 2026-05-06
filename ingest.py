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
import glob
import requests
import fitz
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

# ──────────────────────────────────────────────
# CONFIG — change these to match your files
# ──────────────────────────────────────────────

RESOURCES_DIR = "./resources"         # 👈 Put your PDF files in this folder
CHROMA_DIR = "./chroma_db"            # Where ChromaDB saves data on your disk
COLLECTION_NAME = "privacy_docs"      # Just a name for your document collection

# ──────────────────────────────────────────────
# STEP 1: Load the PDFs
# ──────────────────────────────────────────────

print("📄 Loading PDFs from resources folder and URLs...")
pages = []

if not os.path.exists(RESOURCES_DIR):
    os.makedirs(RESOURCES_DIR)
    print(f"   ⚠️ Created '{RESOURCES_DIR}' directory. Please add your PDF files there if needed.")

pdf_files = glob.glob(os.path.join(RESOURCES_DIR, "*.pdf"))

for pdf_path in pdf_files:
    loader = PyMuPDFLoader(pdf_path)
    pdf_pages = loader.load()
    pages.extend(pdf_pages)
    print(f"   ✅ Loaded {len(pdf_pages)} pages from '{pdf_path}'")

pdf_urls = os.getenv("PDF_URLS")
if pdf_urls:
    urls = [url.strip() for url in pdf_urls.split(",") if url.strip()]
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            doc = fitz.open(stream=response.content, filetype="pdf")
            url_pages = []
            for i, page in enumerate(doc):
                text = page.get_text()
                url_pages.append(Document(
                    page_content=text,
                    metadata={"source": url, "page": i, "total_pages": len(doc)}
                ))
            pages.extend(url_pages)
            print(f"   ✅ Loaded {len(url_pages)} pages from '{url}'")
        except Exception as e:
            print(f"   ⚠️ Warning: Failed to load '{url}': {e}")

if not pages:
    print(f"   ⚠️ No PDFs found in '{RESOURCES_DIR}' and no valid URLs provided. Please add some and run again.")
    exit(0)

print(f"   ✅ Total pages loaded: {len(pages)}")

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
