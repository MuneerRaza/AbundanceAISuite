from langchain_groq import ChatGroq
from langchain_core.messages import RemoveMessage
from models.state import State
from config import SUMMARY_MODEL_ID, MESSAGES_TO_RETAIN

summary_model = ChatGroq(model=SUMMARY_MODEL_ID)

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