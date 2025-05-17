import streamlit as st
import time
from datetime import datetime

def chat_message(message, is_user=False):
    """
    Display a chat message with custom styling
    
    Args:
        message: Message text
        is_user: Whether the message is from the user (True) or AI (False)
    """
    if is_user:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
                <div style="background-color: #673AB7; color: white; padding: 10px 15px; 
                border-radius: 15px 15px 0 15px; max-width: 80%; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
                    {message}
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                <div style="background-color: #F5F5F5; padding: 10px 15px; 
                border-radius: 15px 15px 15px 0; max-width: 80%; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
                    {message}
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )

def chat_avatar_message(message, is_user=False):
    """
    Display a chat message with an avatar
    
    Args:
        message: Message text
        is_user: Whether the message is from the user (True) or AI (False)
    """
    if is_user:
        with st.chat_message("user"):
            st.write(message)
    else:
        with st.chat_message("assistant", avatar="✨"):
            st.write(message)

def stream_response(response_text, speed=0.01):
    """
    Display a streaming effect for AI responses
    
    Args:
        response_text: The complete response text
        speed: Time delay between characters for the streaming effect
    """
    # Create an empty placeholder
    message_placeholder = st.empty()
    full_response = ""
    
    # Stream the response with a typing effect
    for chunk in response_text:
        full_response += chunk
        time.sleep(speed)
        message_placeholder.markdown(full_response + "▌")
    
    # Remove the cursor and display the final response
    message_placeholder.markdown(full_response)
    
    return full_response

def chat_interface(chat_id=None, messages=None, on_message=None, system_prompt=None):
    """
    Complete chat interface with history and input
    
    Args:
        chat_id: Current chat session ID
        messages: List of message objects with 'content' and 'is_user' fields
        on_message: Callback function when a message is sent
        system_prompt: Optional system prompt for the AI
    """
    # Display chat history
    if messages:
        for msg in messages:
            chat_avatar_message(msg["content"], msg["is_user"])
    
    # Chat input
    if chat_id:
        user_message = st.chat_input("Type your message here...")
        
        if user_message:
            # Display user message
            chat_avatar_message(user_message, True)
            
            # Execute callback if provided
            if on_message:
                response = on_message(user_message, system_prompt)

def empty_chat_placeholder():
    """Display a placeholder for empty chat sessions"""
    st.markdown(
        """
        <div style="display: flex; justify-content: center; align-items: center; height: 400px; 
        background-color: #F5F5F5; border-radius: 10px; margin: 20px 0;">
            <div style="text-align: center; color: #757575;">
                <h3>Start a new conversation</h3>
                <p>Your messages will appear here</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def animate_typing():
    """
    Show an animated typing indicator
    """
    # Display a placeholder for the typing animation
    typing_placeholder = st.empty()
    
    # Simulate typing with dots
    dots = [".", "..", "..."]
    for i in range(5):  # Show animation for a few cycles
        for dot in dots:
            typing_placeholder.markdown(f"*Thinking{dot}*")
            time.sleep(0.3)
    
    # Clear the placeholder
    typing_placeholder.empty()
