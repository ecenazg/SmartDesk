"""
rag/retriever.py — FAISS Retrieval Chain
─────────────────────────────────────────
WHAT THIS FILE DOES:
  Loads the FAISS index built by ingest.py and exposes a retrieval
  chain that the agent can call to answer questions from your documents.

HOW RAG WORKS (simply):
  1. User asks: "What is our return policy?"
  2. OpenAI embeds the question into a vector
  3. FAISS finds the 4 most similar document chunks (by vector distance)
  4. Those chunks become the "context" fed to GPT-4o
  5. GPT-4o answers using ONLY that context — no hallucination risk
"""

import os
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

load_dotenv()

FAISS_INDEX_PATH = "./faiss_index"
TOP_K_CHUNKS = 4  # How many chunks to retrieve per query


# ── Prompt Template ───────────────────────────────────────────────────────────
# Explicit instructions prevent the LLM from going "off-script" and hallucinating.

RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are SmartDesk, an AI assistant for internal business operations.
Answer the question using ONLY the context provided below.
If the answer is not in the context, say: "I don't have that information in my knowledge base."

Context:
{context}

Question: {question}

Answer:"""
)


# ── Build Retrieval Chain ─────────────────────────────────────────────────────

def build_retriever():
    """
    Loads FAISS index from disk and returns a RetrievalQA chain.
    Call this once at startup — it's reused for every query.
    """
    if not os.path.exists(FAISS_INDEX_PATH):
        raise FileNotFoundError(
            f"FAISS index not found at '{FAISS_INDEX_PATH}'. "
            "Run `python ingest.py --source ./docs/` first."
        )

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    vectorstore = FAISS.load_local(
        FAISS_INDEX_PATH,
        embeddings,
        allow_dangerous_deserialization=True,  # safe — we built this index ourselves
    )

    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,          # 0 = deterministic; good for factual Q&A
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",     # "stuff" = stuff all chunks into one prompt
        retriever=vectorstore.as_retriever(
            search_kwargs={"k": TOP_K_CHUNKS}
        ),
        chain_type_kwargs={"prompt": RAG_PROMPT},
        return_source_documents=True,  # we'll use these for RAGAS evaluation
    )

    return chain


# ── Query Function ────────────────────────────────────────────────────────────

def query_knowledge_base(chain, question: str) -> dict:
    """
    Run a question through the RAG chain.
    Returns answer text + the source chunks used.
    """
    result = chain.invoke({"query": question})

    return {
        "answer": result["result"],
        "source_docs": result["source_documents"],
        "contexts": [doc.page_content for doc in result["source_documents"]],
    }
