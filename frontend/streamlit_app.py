import streamlit as st
import requests
import json
import os
from datetime import datetime

# Frontend utilities
from utils.state_management import (
    get_auth_token, 
    get_api_url, 
    is_authenticated,
    initialize_session_state
)

# Set page configuration
st.set_page_config(
    page_title="Abundance AI Suite",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
initialize_session_state()

# Main application layout
def main():
    # Custom CSS for styling
    st.markdown("""
    <style>
    .main-title {
        font-size: 3rem !important;
        color: #4527A0;
        text-align: center;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 1.2rem !important;
        color: #5E35B1;
        text-align: center;
        margin-top: 0;
        margin-bottom: 2rem;
    }
    .feature-title {
        font-size: 1.5rem !important;
        color: #512DA8;
        margin-top: 1rem;
    }
    .feature-box {
        background-color: #F5F5F5;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check authentication state
    if not is_authenticated():
        display_landing_page()
    else:
        display_dashboard()

def display_landing_page():
    """Display landing page for unauthenticated users"""
    st.markdown("<h1 class='main-title'>Abundance AI Suite</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Empowering knowledge discovery with AI</p>", unsafe_allow_html=True)
    
    # Hero image or logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("frontend/assets/logo.png", use_column_width=True)
    
    # Feature highlights in columns
    st.markdown("<h2 class='feature-title'>Key Features</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.markdown("### 🤖 AI-Powered Chat")
        st.markdown("""
        Engage with state-of-the-art Large Language Models to get answers, 
        generate content, and explore ideas through natural conversation.
        """)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.markdown("### 📚 Document Intelligence")
        st.markdown("""
        Upload your documents and let our system analyze them. 
        Query specific information from your files and get accurate, 
        contextual answers.
        """)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.markdown("### 🔄 Multiple Chat Sessions")
        st.markdown("""
        Organize your work with multiple chat sessions. Each conversation 
        is stored separately, allowing you to revisit past discussions.
        """)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Call to action
    st.markdown("## Ready to get started?")
    st.markdown("Navigate to the Login/Signup page to begin your journey with Abundance AI Suite.")

def display_dashboard():
    """Display dashboard for authenticated users"""
    st.markdown("<h1 class='main-title'>Welcome to Abundance AI Suite</h1>", unsafe_allow_html=True)
    
    # User info and token balance
    if st.session_state.user_info:
        st.markdown(f"### Welcome, {st.session_state.user_info.get('full_name', 'User')}")
        
        # Token balance
        token_balance = st.session_state.user_info.get('tokens_remaining', 0)
        st.markdown(f"**Tokens remaining**: {token_balance}")
    
    # Quick stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.markdown("### 📊 Your Activity")
        
        # Show user's recent activity
        try:
            if st.session_state.chats:
                st.markdown(f"**Active chat sessions**: {len(st.session_state.chats)}")
            else:
                st.markdown("No active chat sessions yet")
        except:
            st.markdown("Error loading chat sessions")
        
        try:
            if st.session_state.documents:
                st.markdown(f"**Uploaded documents**: {len(st.session_state.documents)}")
            else:
                st.markdown("No documents uploaded yet")
        except:
            st.markdown("Error loading documents")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.markdown("### 🚀 Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ New Chat", use_container_width=True):
                st.switch_page("pages/03_💬_Chat.py")
        
        with col2:
            if st.button("📄 Upload Document", use_container_width=True):
                st.switch_page("pages/04_📄_Manage_Documents.py")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Recent updates or announcements
    st.markdown("### 📣 Recent Updates")
    try:
        # Placeholder for announcements/updates
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.markdown("*No new announcements at this time.*")
        st.markdown("</div>", unsafe_allow_html=True)
    except:
        st.error("Could not load announcements")

if __name__ == "__main__":
    main()
