import streamlit as st
from utils.state_management import initialize_session_state, is_authenticated
# Import your api_client if you need to fetch admin-specific data
# from services import api_client 

initialize_session_state()

def main():
    if not is_authenticated():
        st.warning("Please login to access this page.")
        st.button("Login", on_click=lambda: st.switch_page("pages/02_🔐_Login_Signup.py"))
        st.stop()

    user_info = st.session_state.get("user_info")
    if not user_info or user_info.get("role") != "admin":
        st.error("You do not have permission to access this page.")
        if st.button("Go to Home"):
            st.switch_page("streamlit_app.py") # Assuming your main app page is streamlit_app.py
        st.stop()

    st.set_page_config(
        page_title="Admin Panel - Abundance AI Suite",
        page_icon="👑",
        layout="wide"
    )

    st.title("👑 Admin Panel")
    st.write(f"Welcome, {user_info.get('full_name', 'Admin User')}!")
    
    st.markdown("---")
    st.subheader("Site Management")
    st.write("Placeholder for admin functionalities like:")
    st.markdown("""
    - User Management (View, Edit Roles, Manage Tokens)
    - Document Overview (View all uploaded documents, manage embeddings)
    - System Settings
    - View Logs
    """)

    # Example: User Management Section (requires backend API and api_client function)
    # st.subheader("User Management")
    # success, message, users = api_client.admin_get_all_users() # You would need to implement this
    # if success:
    #     if users:
    #         st.dataframe(users)
    #     else:
    #         st.info("No users found.")
    # else:
    #     st.error(f"Failed to load users: {message}")

if __name__ == "__main__":
    main()
