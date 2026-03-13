"""
ingest.py — SmartDesk Document Ingestion Pipeline
─────────────────────────────────────────────────
WHAT THIS FILE DOES:
  1. Loads PDF and Markdown files from a folder (your "knowledge base")
  2. Splits them into small overlapping chunks (so the AI can find
     relevant pieces without loading entire documents)
  3. Converts each chunk into a vector embedding (a list of numbers
     that captures semantic meaning)
  4. Saves all embeddings into a FAISS index on disk

WHY CHUNKS + EMBEDDINGS?
  Language models have limited context windows. Instead of feeding
  the whole document, RAG finds only the 3-5 most relevant chunks
  and passes just those to the LLM — much cheaper and more accurate.

USAGE:
  python ingest.py --source ./docs/
  python ingest.py --source ./docs/ --index-path ./faiss_index
"""

import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()


# ── Configuration ────────────────────────────────────────────────────────────

CHUNK_SIZE = 500        # Max characters per chunk
CHUNK_OVERLAP = 100     # Characters shared between adjacent chunks
                        # (overlap helps avoid cutting a sentence mid-thought)
FAISS_INDEX_PATH = "./faiss_index"


# ── Document Loaders ─────────────────────────────────────────────────────────

def load_documents(source_dir: str) -> list:
    """
    Walk a directory and load all PDF and Markdown files.
    Returns a flat list of LangChain Document objects.
    """
    docs = []
    source_path = Path(source_dir)

    if not source_path.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    for file_path in source_path.rglob("*"):
        if file_path.suffix.lower() == ".pdf":
            print(f"  📄 Loading PDF: {file_path.name}")
            loader = PyPDFLoader(str(file_path))
            docs.extend(loader.load())

        elif file_path.suffix.lower() in (".md", ".markdown"):
            print(f"  📝 Loading Markdown: {file_path.name}")
            loader = UnstructuredMarkdownLoader(str(file_path))
            docs.extend(loader.load())

    print(f"\n✅ Loaded {len(docs)} document pages/sections from {source_dir}")
    return docs


# ── Text Splitting ────────────────────────────────────────────────────────────

def split_documents(docs: list) -> list:
    """
    Split documents into overlapping chunks.

    RecursiveCharacterTextSplitter tries to split on paragraph breaks
    first, then sentences, then words — keeping chunks semantically clean.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],  # priority order
    )
    chunks = splitter.split_documents(docs)
    print(f"✅ Split into {len(chunks)} chunks "
          f"(size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    return chunks


# ── Embedding + Indexing ──────────────────────────────────────────────────────

def build_faiss_index(chunks: list, index_path: str) -> FAISS:
    """
    Convert chunks to embeddings and store in a FAISS vector index.

    OpenAI's text-embedding-3-small turns each chunk into a 1536-dim vector.
    FAISS (Facebook AI Similarity Search) lets us find the closest vectors
    to a query vector in milliseconds — even over millions of chunks.
    """
    print("\n🔄 Generating embeddings (this calls the OpenAI API)...")

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",  # cheap + high quality
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(index_path)

    print(f"✅ FAISS index saved to: {index_path}/")
    return vectorstore


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SmartDesk document ingestion")
    parser.add_argument("--source", default="./docs/",
                        help="Folder containing PDF/Markdown files")
    parser.add_argument("--index-path", default=FAISS_INDEX_PATH,
                        help="Where to save the FAISS index")
    args = parser.parse_args()

    print("🚀 SmartDesk Ingestion Pipeline\n" + "─" * 40)

    docs = load_documents(args.source)
    if not docs:
        print("⚠️  No documents found. Add PDFs or .md files to the source folder.")
        return

    chunks = split_documents(docs)
    build_faiss_index(chunks, args.index_path)

    print("\n✅ Ingestion complete! Run `python main.py` to start the agent.")


if __name__ == "__main__":
    main()
