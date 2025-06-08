from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class State(TypedDict):
    recent_messages: Annotated[Sequence[BaseMessage], add_messages]
    conversation_summary: str
