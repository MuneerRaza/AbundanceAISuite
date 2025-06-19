from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from services.summarizer import SummarizerNode
from services.rewriter import RewriterNode
from services.call_model import CallModelNode
from models.state import State
from utils.checkpointer import checkpointer
from config import SUMMARY_THRESHOLD, MODEL_ID, UTILS_MODEL_ID

def summary_router(state):
    if len(state.get("recent_messages", [])) > SUMMARY_THRESHOLD:
        return "summarize"
    else:
        return "continue"

model =  ChatGroq(model=MODEL_ID)
utils_model = ChatGroq(model=UTILS_MODEL_ID)
summarizer = SummarizerNode(llm=utils_model)
rewriter = RewriterNode(llm=utils_model)
call_model = CallModelNode(model=model)

def build_workflow():

    workflow = StateGraph(State)
    workflow.add_node("summarize", summarizer.run)
    workflow.add_node("rewrite_query", rewriter.run)
    workflow.add_node("call_model", call_model.invoke)
    workflow.add_conditional_edges(
        START,
        summary_router,
        {
            "summarize": "summarize",
            "continue": "rewrite_query",
        }
    )
    workflow.add_edge("summarize", "rewrite_query")
    workflow.add_edge("rewrite_query", "call_model")
    workflow.add_edge("call_model", END)
    return workflow.compile(checkpointer=checkpointer)
