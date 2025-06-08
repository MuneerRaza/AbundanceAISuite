from langchain_groq import ChatGroq
from config import MODEL_ID, SYSTEM_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

model = ChatGroq(model=MODEL_ID)
chatbot_system_message = SystemMessage(content=SYSTEM_PROMPT)


def prompt_builder(state):
    summary = state.get("conversation_summary", "")
    recent = state.get("recent_messages", [])
    prompt_messages = []
    if summary:
        prompt_messages.append(HumanMessage(
            content=f"Here is a summary of the conversation so far:\n{summary}"
        ))
    prompt_messages.extend(recent)
    return prompt_messages

def call_model(state):
    prompt_with_context = prompt_builder(state)
    response = model.invoke([chatbot_system_message] + prompt_with_context)
    return {"recent_messages": [response]}
