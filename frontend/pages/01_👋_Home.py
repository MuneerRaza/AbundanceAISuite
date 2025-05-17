import streamlit as st
from datetime import datetime

from utils.state_management import is_authenticated, get_auth_token, logout_user

# Set page configuration
st.set_page_config(
    page_title="Home - Abundance AI Suite",
    page_icon="👋",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
<style>
.home-title {
    font-size: 3rem !important;
    color: #4527A0;
    text-align: center;
    margin-bottom: 0;
}
.home-subtitle {
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

def main():
    # Page title
    st.markdown("<h1 class='home-title'>Abundance AI Suite</h1>", unsafe_allow_html=True)
    st.markdown("<p class='home-subtitle'>Your AI-powered knowledge assistant</p>", unsafe_allow_html=True)
    
    # Check authentication
    if is_authenticated():
        display_authenticated_home()
    else:
        display_unauthenticated_home()

def display_authenticated_home():
    """Display home page for authenticated users"""
    # Welcome message with user info
    if st.session_state.user_info:
        user_name = st.session_state.user_info.get("full_name", "User")
        st.success(f"Welcome back, {user_name}!")
    
    # Main features section
    st.markdown("## 🚀 Quick Navigation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.markdown("### 💬 Chat")
        st.markdown("""
        Start a new conversation with AI or continue an existing one.
        Ask questions, generate content, and explore ideas.
        """)
        if st.button("Open Chat", key="open_chat"):
            st.switch_page("pages/03_💬_Chat.py")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.markdown("### 📄 Documents")
        st.markdown("""
        Upload, manage, and query your documents.
        Extract insights and information from your files.
        """)
        if st.button("Manage Documents", key="manage_docs"):
            st.switch_page("pages/04_📄_Manage_Documents.py")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.markdown("### 👤 Profile")
        st.markdown("""
        View and update your profile information.
        Check your token balance and usage history.
        """)
        if st.button("View Profile", key="view_profile"):
            st.switch_page("pages/05_👤_Profile.py")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Admin section (conditional)
    if st.session_state.user_info and st.session_state.user_info.get("role") == "admin":
        st.markdown("## 🔧 Admin Tools")
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.markdown("""
        As an administrator, you have access to additional tools:
        
        - Manage users
        - Monitor system usage
        - Adjust token allocations
        - Upload global documents
        """)
        if st.button("Open Admin Panel"):
            st.switch_page("pages/06_⚙️_Admin_Panel.py")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Account section with logout
    st.sidebar.markdown("## 👤 Account")
    if st.sidebar.button("Logout"):
        logout_user()
        st.experimental_rerun()

def display_unauthenticated_home():
    """Display home page for unauthenticated users"""
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
    st.markdown("## Get Started")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", use_container_width=True):
            st.switch_page("pages/02_🔐_Login_Signup.py")
    
    with col2:
        if st.button("Sign Up", use_container_width=True):
            st.session_state.show_signup = True
            st.switch_page("pages/02_🔐_Login_Signup.py")

if __name__ == "__main__":
    main()
