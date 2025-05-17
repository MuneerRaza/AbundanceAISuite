import streamlit as st
from datetime import datetime
import time

from services.api_client import create_chat_session, get_chat_sessions, get_chat_history, send_chat_message
from utils.state_management import (
    is_authenticated, set_current_chat, get_current_chat, 
    set_chats, add_message_to_chat, get_chat_messages
)
from components.chat_display import chat_interface, empty_chat_placeholder, chat_avatar_message

# Set page configuration
st.set_page_config(
    page_title="Chat - Abundance AI Suite",
    page_icon="💬",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.chat-header {
    font-size: 1.5rem !important;
    color: #4527A0;
    margin-bottom: 10px;
}
.chat-list {
    background-color: #F5F5F5;
    border-radius: 10px;
    padding: 10px;
    margin-bottom: 10px;
    cursor: pointer;
}
.chat-list-item {
    padding: 8px 10px;
    border-radius: 5px;
    margin: 5px 0;
}
.chat-list-item:hover {
    background-color: #E0E0E0;
}
.chat-list-item-selected {
    background-color: #D1C4E9;
    border-left: 4px solid #673AB7;
}
.main-chat-container {
    height: 600px;
    overflow-y: auto;
    padding: 20px;
    background-color: #FAFAFA;
    border-radius: 10px;
    border: 1px solid #EEEEEE;
}
.system-prompt-container {
    background-color: #F5F5F5;
    border-radius: 5px;
    padding: 10px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

def main():
    # Redirect if not authenticated
    if not is_authenticated():
        st.warning("Please login to access the chat feature.")
        st.button("Login", on_click=lambda: st.switch_page("pages/02_🔐_Login_Signup.py"))
        return
    
    # Page title
    st.markdown("<h1>💬 AI Chat</h1>", unsafe_allow_html=True)
    
    # Layout: Sidebar for chat list, main area for chat
    initialize_chat_state()
    
    # Create a two-column layout
    chat_list_col, chat_window_col = st.columns([1, 3])
    
    with chat_list_col:
        display_chat_sidebar()
    
    with chat_window_col:
        display_chat_window()

def initialize_chat_state():
    """Initialize chat-related session state variables"""
    # Fetch existing chats if not already loaded
    if "chats_loaded" not in st.session_state or not st.session_state.chats_loaded:
        load_user_chats()
        st.session_state.chats_loaded = True
    
    # Initialize system prompt if not exists
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = "You are a helpful AI assistant."
    
    # Initialize RAG toggle if not exists
    if "use_rag" not in st.session_state:
        st.session_state.use_rag = True

def load_user_chats():
    """Fetch and load user's chat sessions"""
    success, message, chats = get_chat_sessions()
    
    if success:
        # Sort chats by updated_at (most recent first)
        sorted_chats = sorted(chats, key=lambda x: x.get("updated_at", ""), reverse=True)
        set_chats(sorted_chats)
        
        # Set current chat if not set
        if not get_current_chat() and sorted_chats:
            set_current_chat(str(sorted_chats[0]["_id"]))
            load_chat_messages(str(sorted_chats[0]["_id"]))
    else:
        st.error(f"Failed to load chats: {message}")
        set_chats([])

def load_chat_messages(chat_id):
    """Load messages for a specific chat session"""
    # Don't reload if already loaded
    if chat_id in st.session_state.chat_messages and st.session_state.chat_messages[chat_id]:
        return
    
    success, message, messages = get_chat_history(chat_id)
    
    if success:
        # Convert to format expected by chat display
        formatted_messages = []
        for msg in reversed(messages):  # Reverse to get chronological order
            # User message
            formatted_messages.append({
                "content": msg["message"],
                "is_user": True,
                "timestamp": msg.get("timestamp", "")
            })
            # AI response
            formatted_messages.append({
                "content": msg["response"],
                "is_user": False,
                "timestamp": msg.get("timestamp", "")
            })
        
        # Set in session state
        st.session_state.chat_messages[chat_id] = formatted_messages

def display_chat_sidebar():
    """Display chat list and controls in sidebar"""
    # New Chat button
    if st.button("➕ New Chat", use_container_width=True):
        show_new_chat_dialog()
    
    st.markdown("<div class='chat-header'>Your Chats</div>", unsafe_allow_html=True)
    
    # Display chat sessions
    if st.session_state.chats:
        st.markdown("<div class='chat-list'>", unsafe_allow_html=True)
        
        for chat in st.session_state.chats:
            chat_id = str(chat["_id"])
            is_selected = get_current_chat() == chat_id
            
            # Format title and date
            title = chat.get("title", "Untitled Chat")
            date_str = ""
            if "updated_at" in chat:
                try:
                    date = datetime.fromisoformat(chat["updated_at"].replace("Z", "+00:00"))
                    date_str = date.strftime("%m/%d/%Y")
                except:
                    date_str = ""
            
            # Create a clickable chat item
            if st.button(
                f"{title}\n{date_str}",
                key=f"chat_{chat_id}",
                use_container_width=True,
                type="secondary" if not is_selected else "primary"
            ):
                set_current_chat(chat_id)
                load_chat_messages(chat_id)
                st.experimental_rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No chat sessions found.")

def display_chat_window():
    """Display the main chat interface"""
    chat_id = get_current_chat()
    
    if not chat_id:
        st.info("Select or create a chat to begin.")
        return
    
    # Get current chat details
    current_chat = next((c for c in st.session_state.chats if str(c["_id"]) == chat_id), None)
    if not current_chat:
        st.error("Selected chat not found.")
        return
    
    # Display chat title
    st.markdown(f"<h2>{current_chat.get('title', 'Untitled Chat')}</h2>", unsafe_allow_html=True)
    
    # Settings expander
    with st.expander("Chat Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            # System prompt input
            st.text_area(
                "System Prompt",
                value=st.session_state.system_prompt,
                key="system_prompt_input",
                height=100,
                help="Custom instructions for the AI assistant"
            )
            
            # Update system prompt when changed
            if "system_prompt_input" in st.session_state:
                st.session_state.system_prompt = st.session_state.system_prompt_input
        
        with col2:
            # RAG toggle
            st.checkbox(
                "Use Document Knowledge",
                value=st.session_state.use_rag,
                key="use_rag_toggle",
                help="When enabled, the AI will search your uploaded documents for relevant information"
            )
            
            # Update RAG setting when toggled
            if "use_rag_toggle" in st.session_state:
                st.session_state.use_rag = st.session_state.use_rag_toggle
    
    # Load messages if not already loaded
    load_chat_messages(chat_id)
    
    # Display chat messages
    messages = get_chat_messages(chat_id)
    
    if not messages:
        empty_chat_placeholder()
    
    # Chat interface
    for msg in messages:
        chat_avatar_message(msg["content"], msg["is_user"])
    
    # Chat input
    user_message = st.chat_input("Type your message here...")
    
    if user_message:
        # Show user message immediately
        chat_avatar_message(user_message, True)
        
        # Send message to API
        with st.status("Generating response..."):
            success, error_message, response_data = send_chat_message(
                chat_id=chat_id,
                message=user_message,
                system_prompt=st.session_state.system_prompt,
                use_rag=st.session_state.use_rag
            )
        
        if success:
            # Display AI response
            chat_avatar_message(response_data["response"], False)
            
            # Update tokens in UI
            st.toast(f"Used {response_data['tokens_used']} tokens. {response_data['remaining_tokens']} remaining.")
            
            # Store messages in session state
            add_message_to_chat(chat_id, user_message, True)
            add_message_to_chat(chat_id, response_data["response"], False)
        else:
            st.error(f"Error: {error_message}")

def show_new_chat_dialog():
    """Show a dialog to create a new chat"""
    st.session_state.show_new_chat = True
    
    # Modal-like dialog
    with st.container():
        st.subheader("Create New Chat")
        chat_title = st.text_input("Chat Title", value="New Chat", key="new_chat_title_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Cancel", key="cancel_new_chat"):
                st.session_state.show_new_chat = False
                st.experimental_rerun()
        
        with col2:
            if st.button("Create", key="confirm_new_chat"):
                if chat_title:
                    # Create new chat via API
                    success, message, chat_data = create_chat_session(chat_title)
                    
                    if success:
                        # Update session state
                        st.session_state.chats.insert(0, chat_data)  # Add to beginning
                        set_current_chat(str(chat_data["_id"]))
                        st.success("Chat created successfully!")
                    else:
                        st.error(f"Failed to create chat: {message}")
                
                # Reset state and refresh
                st.session_state.show_new_chat = False
                st.experimental_rerun()

if __name__ == "__main__":
    main()
