import streamlit as st
import time

from services.api_client import login_user, register_user, get_user_info
from utils.state_management import set_auth_token, set_user_info, is_authenticated, initialize_session_state

# Set page configuration
st.set_page_config(
    page_title="Login/Signup - Abundance AI Suite",
    page_icon="🔐",
    layout="centered"
)

# Custom CSS for styling
st.markdown("""
<style>
.auth-container {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
    margin-top: 20px;
}
.auth-header {
    font-size: 1.8rem;
    color: #4527A0;
    text-align: center;
    margin-bottom: 20px;
}
.auth-subheader {
    font-size: 1rem;
    color: #5E35B1;
    text-align: center;
    margin-bottom: 20px;
}
.success-message {
    background-color: #d1e7dd;
    color: #0f5132;
    padding: 10px;
    border-radius: 5px;
    margin: 10px 0;
    text-align: center;
}
.error-message {
    background-color: #f8d7da;
    color: #842029;
    padding: 10px;
    border-radius: 5px;
    margin: 10px 0;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

def main():
    initialize_session_state()  # Initialize session state here

    # Check if user is already authenticated
    if is_authenticated():
        st.warning("You are already logged in.")
        if st.button("Go to Home"):
            st.switch_page("streamlit_app.py")
        return
    
    # Page title
    st.markdown("<h1 class='auth-header'>Welcome to Abundance AI Suite</h1>", unsafe_allow_html=True)
    st.markdown("<p class='auth-subheader'>Please log in or sign up to continue</p>", unsafe_allow_html=True)
    
    # Create tabs for login and signup
    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])
    
    # Handle login
    with login_tab:
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        st.markdown("<h2>Login</h2>", unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    # Show loading indicator
                    with st.spinner("Logging in..."):
                        success, message, data = login_user(email, password)
                    
                    if success:
                        # Set authentication token
                        set_auth_token(data["access_token"], expiry_minutes=60)
                        
                        # Get user info
                        success, user_data = get_user_info()
                        if success:
                            set_user_info(user_data)
                            
                            # Show success message
                            st.markdown("<div class='success-message'>Login successful! Redirecting...</div>", unsafe_allow_html=True)
                            time.sleep(1)
                            st.switch_page("streamlit_app.py")
                        else:
                            st.error("Failed to retrieve user information.")
                    else:
                        st.markdown(f"<div class='error-message'>{message}</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Handle signup
    with signup_tab:
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        st.markdown("<h2>Sign Up</h2>", unsafe_allow_html=True)
        
        # Signup form
        with st.form("signup_form"):
            full_name = st.text_input("Full Name", placeholder="Enter your full name")
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Create a password (min 8 characters)")
            password_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            submit_button = st.form_submit_button("Sign Up")
            
            if submit_button:
                # Validate input
                if not full_name or not email or not password:
                    st.error("Please fill in all fields.")
                elif password != password_confirm:
                    st.error("Passwords do not match.")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters long.")
                else:
                    # Show loading indicator
                    with st.spinner("Creating your account..."):
                        success, message, data = register_user(email, password, full_name)
                    
                    if success:
                        st.markdown("<div class='success-message'>Account created successfully! Please log in.</div>", unsafe_allow_html=True)
                        st.session_state.show_login = True
                        st.rerun() # Changed from st.experimental_rerun()
                    else:
                        st.markdown(f"<div class='error-message'>{message}</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
