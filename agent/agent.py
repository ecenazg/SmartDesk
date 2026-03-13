"""
agent/agent.py — LangChain Agent Definition
────────────────────────────────────────────
WHAT THIS FILE DOES:
  Wires together the LLM, tools, memory, and system prompt into a
  single LangChain agent that the main.py loop interacts with.

AGENT TYPE — "openai-tools":
  This agent uses OpenAI's native function-calling API.
  Instead of parsing text like older ReAct agents, GPT-4o returns
  a structured JSON object saying exactly which tool to call and
  with what arguments. Much more reliable than text parsing.

MEMORY:
  ConversationBufferWindowMemory keeps the last K exchanges in context.
  The agent can refer back to earlier messages in the conversation.
"""

import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent.prompts import SYSTEM_PROMPT
from agent.tools import ALL_TOOLS, set_rag_chain
from rag.retriever import build_retriever
from logging.audit_logger import AuditLogger

load_dotenv()


def build_agent() -> AgentExecutor:
    """
    Build and return the SmartDesk agent executor.
    Call once at startup — this is the main entry point for agent interactions.
    """

    # 1. Load RAG chain and inject into tools module
    print("🔄 Loading RAG retriever...")
    try:
        rag_chain = build_retriever()
        set_rag_chain(rag_chain)
        print("✅ Knowledge base loaded")
    except FileNotFoundError as e:
        print(f"⚠️  {e}")
        print("   Agent will run without knowledge base until ingest.py is run.\n")

    # 2. Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.1,        # slight creativity for conversational flow
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        streaming=True,         # stream tokens to terminal as they generate
    )

    # 3. Build the prompt template
    # MessagesPlaceholder slots are filled by LangChain automatically:
    #   - chat_history: from memory
    #   - agent_scratchpad: the agent's internal reasoning steps
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    # 4. Create the agent (binds LLM + tools + prompt together)
    agent = create_openai_tools_agent(llm, ALL_TOOLS, prompt)

    # 5. Wrap in AgentExecutor (handles the tool-call loop)
    executor = AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        memory=ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10,               # remember last 10 exchanges
        ),
        verbose=True,           # print agent reasoning to terminal (great for learning!)
        max_iterations=5,       # safety cap — prevents infinite tool loops
        handle_parsing_errors=True,
    )

    return executor


def run_agent(executor: AgentExecutor, user_input: str, logger: AuditLogger) -> str:
    """
    Run a single turn of the agent, log the interaction, and trace to Langfuse.
    Returns the agent's final response string.
    """
    from logging.langfuse_tracer import get_langfuse_callback

    logger.log_input(user_input)

    # Attach Langfuse callback if configured — no-op if not set up
    langfuse_cb = get_langfuse_callback()
    config = {"callbacks": [langfuse_cb]} if langfuse_cb else {}

    result   = executor.invoke({"input": user_input}, config=config)
    response = result.get("output", "")

    logger.log_output(response)
    return response
