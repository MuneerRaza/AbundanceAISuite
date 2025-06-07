import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated
    
from config import MODEL_ID, K_LAST_MESSAGES

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pymongo import MongoClient
from langgraph.checkpoint.mongodb import MongoDBSaver

load_dotenv()
DB_URI = os.getenv("DB_URI")

chatbot_system_message = SystemMessage(content=(""" 
You are a helpful and knowledgeable chatbot assistant. 
Your goal is to provide clear and accurate answers to user questions based on the information they provide. 
Stay focused, concise, and ensure your responses are relevant to the context of the conversation. 
If you don't have enough information, ask for clarification."""))

model = ChatGroq(model=MODEL_ID)
client = MongoClient(DB_URI)
checkpointer = MongoDBSaver(client, db_name="abundanci_ai")

class State(TypedDict):
    messages: Annotated[list, add_messages]
    question: str
    answer: str

class SummaryState(State):
    summary: str


def call_model(state: SummaryState) -> SummaryState:
    summary = state.get("summary", "")
    if summary:
        summary_message = SystemMessage(content=(
            f"Summary of the conversation:\n\n{summary}"
        ))

        messages_with_summary = [summary_message] + state["messages"]

    else:
        messages_with_summary = state["messages"]
    
    question = HumanMessage(content=state.get("question", ""))
    response = model.invoke([chatbot_system_message] + messages_with_summary + [question])
    if not isinstance(response, AIMessage):
        response_message = AIMessage(content=str(response.content))
    else:
        response_message = response
    answer_str = response.content if isinstance(response.content, str) else str(response.content)
    return SummaryState(
        messages=[question, response_message],
        question=state.get("question", ""),
        answer=answer_str,
        summary=state.get("summary", "")
    )

def summarize(state: SummaryState) -> SummaryState:
    summary = state.get("summary", "")
    # no system message
    # the order of components is important

    if summary:
        summary_message = HumanMessage(content=(f"""
            Expand the summary below by incorporating the above conversation while preserving context, key points, and 
            user intent. Rework the summary if needed. Ensure that no critical information is lost and that the 
            conversation can continue naturally without gaps. Keep the summary concise yet informative, removing 
            unnecessary repetition while maintaining clarity.
            Make sure that summary is not too long, it must be concise.
            
            Only return the updated summary. Do not add explanations, section headers, or extra commentary.

            Existing summary:

            {summary}
            """)
        )
        
    else:
        summary_message = HumanMessage(content="""
        Summarize the above conversation while preserving full context, key points, and user intent. Your response 
        should be concise yet detailed enough to ensure seamless continuation of the discussion. Avoid redundancy, 
        maintain clarity, and retain all necessary details for future exchanges.
                                       
        Only return the summarized content. Do not add explanations, section headers, or extra commentary.
        """)

    # Add prompt to our history
    messages = state["messages"] + [summary_message]
    response = model.invoke(messages)
    
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-K_LAST_MESSAGES]]
    
    return SummaryState(
        messages = delete_messages,
        question = state.get("question", None),
        answer = state.get("answer", None),
        summary = response.content if isinstance(response.content, str) else str(response.content)
    )

def summary_router(state: SummaryState):
    messages = state["messages"]
    
    if len(messages) > K_LAST_MESSAGES:
        return "summarize"
    
    return END

workflow = StateGraph(SummaryState)
workflow.add_node(call_model)
workflow.add_node(summarize)

workflow.add_edge(START, "call_model")
workflow.add_conditional_edges("call_model", summary_router)
workflow.add_edge("summarize", END)

graph = workflow.compile(checkpointer=checkpointer)

config = RunnableConfig({
    "configurable": {            
        "thread_id": "1"
    }
})
state = {"messages": []}
while True:
    input_text = input("You: ")
    if input_text.lower() == "q":
        break

    state["messages"].append({"role": "user", "content": input_text})
    response = graph.invoke(state, config=config)
    print(response["messages"][-1])