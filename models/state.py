from typing import TypedDict, Annotated, Sequence, List
from langchain_core.messages import BaseMessage
from langchain.schema import Document
from langgraph.graph.message import add_messages

class State(TypedDict):
    recent_messages: Annotated[Sequence[BaseMessage], add_messages]
    conversation_summary: str
    rewritten_query: str
    tasks: List[str]
    web_search_results: str
    retrieved_docs: List[Document]
    final_context: str