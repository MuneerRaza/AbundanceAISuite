from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from models.state import State

class RewriterNode:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.system_prompt = (
            "You are an expert AI assistant specializing in search query optimization. "
            "Your task is to rewrite a user's query to be clear, concise, and optimal "
            "for information retrieval. "
            "- Preserve the core intent of the original query. "
            "- Clarify ambiguities and resolve pronouns. "
            "- Expand acronyms to their full form where appropriate. "
            "- Do not add new information or make assumptions that are not "
            "explicitly present in the user's query. "
            "- The rewritten query should be a direct, searchable phrase."
        )

    def run(self, state:State) -> Dict[str, Any]:
        
        last_user_message = state["recent_messages"][-1].content
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=last_user_message),
        ]

        response = self.llm.invoke(messages)
        return {"rewritten_query": response.content}
