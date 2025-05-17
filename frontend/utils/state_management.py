import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta

# API URL configuration
API_URL = "http://localhost:8000/api/v1"

def get_api_url():
    """Get the base API URL"""
    return API_URL

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if "token" not in st.session_state:
        st.session_state.token = None
    
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    
    if "token_expiry" not in st.session_state:
        st.session_state.token_expiry = None
    
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    
    if "chats" not in st.session_state:
        st.session_state.chats = []
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = {}
    
    if "documents" not in st.session_state:
        st.session_state.documents = []

def is_authenticated():
    """Check if the user is authenticated and token is still valid"""
    if not st.session_state.token:
        return False
    
    # Check token expiry
    if st.session_state.token_expiry and datetime.now() > st.session_state.token_expiry:
        # Token has expired
        logout_user()
        return False
    
    return True

def set_auth_token(token, expiry_minutes=60):
    """Set authentication token and expiry"""
    st.session_state.token = token
    st.session_state.token_expiry = datetime.now() + timedelta(minutes=expiry_minutes)

def get_auth_token():
    """Get the authentication token"""
    return st.session_state.token

def get_auth_headers():
    """Get authentication headers for API requests"""
    token = get_auth_token()
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}

def set_user_info(user_info):
    """Set user info in session state"""
    st.session_state.user_info = user_info

def logout_user():
    """Clear authentication data"""
    st.session_state.token = None
    st.session_state.user_info = None
    st.session_state.token_expiry = None
    st.session_state.current_chat_id = None
    st.session_state.chats = []
    st.session_state.chat_messages = {}
    st.session_state.documents = []

def set_current_chat(chat_id):
    """Set the current active chat session"""
    st.session_state.current_chat_id = chat_id

def get_current_chat():
    """Get the current active chat session"""
    return st.session_state.current_chat_id

def set_chats(chats):
    """Set available chat sessions"""
    st.session_state.chats = chats
    
    # Initialize messages dict if it doesn't exist
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = {}
    
    # Initialize empty messages for new chats
    for chat in chats:
        chat_id = str(chat["_id"])
        if chat_id not in st.session_state.chat_messages:
            st.session_state.chat_messages[chat_id] = []

def add_message_to_chat(chat_id, message, is_user=True):
    """Add a message to a chat session"""
    # Ensure chat exists in messages dict
    if chat_id not in st.session_state.chat_messages:
        st.session_state.chat_messages[chat_id] = []
    
    st.session_state.chat_messages[chat_id].append({
        "content": message,
        "is_user": is_user,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })

def get_chat_messages(chat_id):
    """Get messages for a specific chat session"""
    return st.session_state.chat_messages.get(chat_id, [])

def set_documents(documents):
    """Set available documents"""
    st.session_state.documents = documents
