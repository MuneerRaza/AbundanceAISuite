# project/services/decompose_node.py

from typing import Dict, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, Field
from models.state import State

# The Pydantic schema remains the same
class DecomposedTasks(BaseModel):
    """A list of tasks that need to be accomplished to answer the user's query."""
    tasks: List[str] = Field(
        ..., 
        description="A list of smaller, self-contained, answerable tasks derived from the user's query."
    )

class DecomposeNode:
    """
    A node that decomposes the rewritten query into a series of tasks or steps
    using structured output for guaranteed JSON formatting.
    """
    def __init__(self, llm: BaseChatModel):
        # 1. (CORRECTED) Rename variable for clarit        
        self.structured_llm = llm.with_structured_output(DecomposedTasks)
        
        # 2. (CORRECTED) The system prompt now correctly instructs on format, not tool use.
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert at breaking down complex user questions into a series of smaller, "
                    "answerable tasks. Your goal is to create a clear, step-by-step plan. "
                    "If the question is simple and can be answered in a single step, just return that single task. "
                    "Do not create unnecessary sub-tasks. "
                    "You must format your output as a JSON object that adheres to the `DecomposedTasks` schema.",
                ),
                (
                    "human",
                    "Decompose the following user query into a concise list of tasks: '{query}'",
                ),
            ]
        )

    def invoke(self, state: State) -> Dict[str, List[str]]:
        """
        Decomposes the query and updates the state with a list of tasks.
        """
        response_tasks: DecomposedTasks = DecomposedTasks(tasks=[])
        rewritten_query = state.get("rewritten_query", "")
        if not rewritten_query:
            return {"tasks": []}
            
        print("---DECOMPOSING TASK (WITH STRUCTURED OUTPUT)---")
        chain = self.prompt | self.structured_llm
        try:
            response_tasks = chain.invoke({"query": rewritten_query})
            print(f"Decomposed into tasks: {response_tasks.tasks}")
            return {"tasks": response_tasks.tasks}
        except Exception as e:
            print(f"Error during structured output decomposition: {e}")
            return {"tasks": [rewritten_query]}