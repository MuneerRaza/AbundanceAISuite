import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated, Sequence

from config import MODEL_ID, SUMMARY_MODEL_ID, SUMMARY_THRESHOLD, MESSAGES_TO_RETAIN

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pymongo import MongoClient
from langgraph.checkpoint.mongodb import MongoDBSaver

# --- Configuration and Setup ---
load_dotenv()
DB_URI = os.getenv("DB_URI")

# System prompt for the main chatbot
chatbot_system_message = SystemMessage(content=(
    "You are an Converstational expert AI assistant. Your task is to answer user's query, provide accurate and concise answers by synthesizing the provided context (conversation summary and recent messages)."
    "Key Directives:"
    "- If context is insufficient to answer accurately, you must ask for clarification instead of inventing information."
    "- Act as if you have a perfect, natural memory. NEVER allude to, mention, or reveal the existence of the 'summary' in your responses. Until user explicitly mentions."
))

model = ChatGroq(model=MODEL_ID)
summary_model = ChatGroq(model=SUMMARY_MODEL_ID)
client = MongoClient(DB_URI)

checkpointer = MongoDBSaver(client, db_name='abundance_ai')

class State(TypedDict):
    recent_messages: Annotated[Sequence[BaseMessage], add_messages]
    
    conversation_summary: str


def prompt_builder(state: State) -> list[BaseMessage]:
    summary = state.get("conversation_summary", "")
    recent = state.get("recent_messages", [])
    
    prompt_messages = []
    if summary:
        print(summary)
        prompt_messages.append(HumanMessage(
            content=f"Here is a summary of the conversation so far:\n{summary}"
        ))
    
    prompt_messages.extend(recent)
    return prompt_messages

def call_model(state: State) -> dict:

    prompt_with_context = prompt_builder(state)
    response = model.invoke([chatbot_system_message] + prompt_with_context)
    return {"recent_messages": [response]}

def summarizer(state: State) -> dict:
    summary = state.get("conversation_summary", "")
    all_recent_messages  = state.get("recent_messages", [])
    messages_to_summarize = all_recent_messages[:-MESSAGES_TO_RETAIN]
    
    if not messages_to_summarize:
        return {}

    conversation_chunk = "\n".join(f"{msg.type}: {msg.content}" for msg in messages_to_summarize)
    if not summary or summary == "":
        prompt = (
            f"""
            **Role:** You are a Knowledge Architect AI that converts dialogues into structured, categorized fact sheets.

            **Instructions:**
            - Analyze the provided conversation chunk.
            - Derive relevant category headings from the dialogue's context.
            - Under each heading, list key facts as short, declarative bullet points. Attribute facts to specific people or goals where applicable.
            - **Factuality is paramount:** Only include explicitly stated facts. Do not add assumptions or outside information.
            - **Signal over Noise:** Ignore conversational filler, greetings, and obvious statements. Extract only meaningful, non-redundant information.
            - **Obvious Facts:** Do not include facts that are already well-known or obvious.
            **Output Format:**
            - The output MUST be only the Markdown fact sheet. Do not include any other text.
            - Follow this structure:
            ### [Derived Category 1]
            - [Extracted detail]
            ...
            ### [Derived Category 2]
            -  [Another detail]
            ...

            **Conversation to Analyze:**
            {conversation_chunk}

            **Structured Fact Sheet Output:**
            """
        )
    else:
        prompt = (
            f"""
            **Role:** You are a Knowledge Architect AI responsible for updating an existing fact sheet with new information from a dialogue.

            **Task:** Your goal is to seamlessly integrate new information to produce a single, updated, concise, and coherent knowledge base.

            **Critical Update Rules:**
            - **Analyze & Integrate:** Carefully analyze the existing fact sheet and the new conversation messages.
            - **Integrate & Categorize:** Add new facts under the most relevant existing heading, or create a new one if necessary.
            - **Revise, Don't Contradict:** If new information clarifies or corrects an old fact, you MUST modify the existing fact instead of adding a new one.
            - **No Duplicates:** You MUST NOT add facts that are already present or redundant.
            - **Maintain Factuality:** Do not assume or invent information.

            **Output Format:**
            - The output MUST be the complete, updated fact sheet formatted in Markdown. Do not add any other text.

            **Existing Fact Sheet:**
            {summary}

            **New Conversation Messages:**
            {conversation_chunk}

            **Direct Updated Fact Sheet Output:**
            """
        )

    new_summary = summary_model.invoke(prompt).content
    
    
    messages_to_delete = [
    RemoveMessage(id=m.id) for m in messages_to_summarize if m.id is not None
    ]

    return {
        "conversation_summary": new_summary,
        "recent_messages": messages_to_delete, # This is the list of deletion commands
    }

def summary_router(state: State) -> str:
    """Decides whether to summarize based on the number of recent messages."""
    if len(state.get("recent_messages", [])) > SUMMARY_THRESHOLD:
        print("Summarizing conversation...")
        return "summarize"
    else:
        print("Continuing without summarization...")
        return "continue"

workflow = StateGraph(State)

workflow.add_node("summarize", summarizer)
workflow.add_node("call_model", call_model)

workflow.add_conditional_edges(
    START,
    summary_router,
    {
        "summarize": "summarize",
        "continue": "call_model",
    }
)

workflow.add_edge("summarize", "call_model")
workflow.add_edge("call_model", END)

graph = workflow.compile(checkpointer=checkpointer)

config = RunnableConfig(configurable={"thread_id": "1"})
print("Abundance AI! Type 'q' to quit.")
while True:
    user_input = input("You: ")
    if user_input.lower() == "q":
        break
    
    input_msg = HumanMessage(content=user_input)
    response = graph.invoke(
        {"recent_messages": [input_msg]},
        config=config
    )
    print(f"Bot: {response['recent_messages'][-1].content}")