# from config import SYSTEM_PROMPT
# from langchain_core.messages import SystemMessage, HumanMessage
# from langchain_core.language_models.chat_models import BaseChatModel
# from models.state import State

# class CallModelNode:
#     def __init__(self, model: BaseChatModel):
#         self.model = model
#         self.system_prompt = SYSTEM_PROMPT

#     def _build_prompt(self, state: State):
#         summary = state.get("conversation_summary", "")
#         recent = state.get("recent_messages", [])
#         prompt_messages = []
#         if summary:
#             prompt_messages.append(HumanMessage(
#                 content=f"Here is a summary of the conversation for context:\n{summary}"
#             ))
#         prompt_messages.extend(recent)
#         return prompt_messages
    
#     def invoke(self, state: State):
#         prompt_with_context = self._build_prompt(state)
#         response = self.model.invoke([SystemMessage(content=self.system_prompt)] + prompt_with_context)
#         return {"recent_messages": [response]}

# project/services/call_model.py

from typing import Sequence, List
from models.state import State
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langchain_core.language_models.chat_models import BaseChatModel

# A helper to format the recent messages
def format_recent_messages(messages: Sequence[BaseMessage]) -> str:
    """Formats a list of messages into a human-readable string."""
    if not messages:
        return "No recent conversation history."
    return "\n".join([f"{msg.type.capitalize()}: {msg.content}" for msg in messages])


class CallModelNode:
    def __init__(self, model: BaseChatModel):
        self.model = model
        self.system_prompt = (
            "You are an expert AI assistant. Your task is to synthesize the provided context to answer the user's question accurately and concisely. "
            "The context may include a summary of past conversations, information from documents, and web searches. "
            "First, consider the summary for long-term context. Then, review the retrieved information. Finally, consider the immediate conversation history to understand the user's latest question fully. "
            "Directly answer the user's final question based on all available information. "
            "If the context is insufficient, clearly state that you could not find the answer in the provided information. "
            "Do not mention the words 'context', 'documents', or 'web search' in your response. "
            "Cite your sources using the format [Source: path/to/document.pdf] where applicable."
        )

    def _build_prompt(self, state: State) -> List[BaseMessage]:
        """
        Builds the prompt for the final answer synthesis, using the summary,
        aggregated context, and recent conversation history.
        """
        final_context = state.get("final_context", "No context provided.")
        summary = state.get("conversation_summary", "")
        recent_messages = state.get("recent_messages", [])

        # 1. Dynamically build the System Prompt with the long-term summary
        system_content = self.system_prompt
        if summary:
            system_content += f"\n\n---SUMMARY OF PAST CONVERSATION---\n{summary}"

        # 2. Format the recent messages to include the conversational flow
        formatted_history = format_recent_messages(recent_messages)
        
        # 3. Construct a clear Human Prompt with all pieces of information
        human_prompt = (
            f"Please provide a comprehensive answer to the last user question, using the context and conversation history provided.\n\n"
            f"---RETRIEVED CONTEXT---\n{final_context}\n\n"
            f"---RECENT CONVERSATION HISTORY---\n{formatted_history}"
        )
        
        return [
            SystemMessage(content=system_content),
            HumanMessage(content=human_prompt)
        ]
    
    def invoke(self, state: State):
        """
        Invokes the final model to generate an answer based on all available context.
        """
        print("---GENERATING FINAL RESPONSE---")
        prompt_with_context = self._build_prompt(state)
        response = self.model.invoke(prompt_with_context)
        return {"recent_messages": [response]}