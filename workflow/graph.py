from langgraph.graph import StateGraph, START, END
from services.summarizer import summarizer
from services.model_caller import call_model
from models.state import State
from utils.checkpointer import checkpointer
from config import SUMMARY_THRESHOLD

def summary_router(state):
    if len(state.get("recent_messages", [])) > SUMMARY_THRESHOLD:
        return "summarize"
    else:
        return "continue"

def build_workflow():
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
    return workflow.compile(checkpointer=checkpointer)
