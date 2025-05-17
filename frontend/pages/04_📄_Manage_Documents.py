import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io
import time

from services.api_client import get_user_documents, upload_document, process_document, delete_document
from utils.state_management import is_authenticated, set_documents

# Set page configuration
st.set_page_config(
    page_title="Manage Documents - Abundance AI Suite",
    page_icon="📄",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.document-title {
    font-size: 1.2rem !important;
    font-weight: bold;
    color: #512DA8;
}
.document-box {
    background-color: #F5F5F5;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
    border-left: 4px solid #673AB7;
}
.document-info {
    font-size: 0.9rem;
    color: #666;
    margin: 5px 0;
}
.document-actions {
    margin-top: 10px;
}
.document-metadata {
    font-size: 0.8rem;
    color: #777;
}
.status-embedded {
    color: #4CAF50;
    font-weight: bold;
}
.status-pending {
    color: #FF9800;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

def main():
    # Redirect if not authenticated
    if not is_authenticated():
        st.warning("Please login to access document management.")
        st.button("Login", on_click=lambda: st.switch_page("pages/02_🔐_Login_Signup.py"))
        return
    
    # Page title
    st.markdown("<h1>📄 Document Management</h1>", unsafe_allow_html=True)
    
    # Document upload section
    with st.expander("Upload New Document", expanded=True):
        display_upload_form()
    
    # Document list section
    st.markdown("## Your Documents")
    display_documents()

def display_upload_form():
    """Display the document upload form"""
    st.markdown("""
    Upload documents to use with the AI assistant. 
    The system will analyze and index your documents for accurate retrieval.
    """)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a file to upload",
            type=["pdf", "txt", "csv", "docx", "doc"],
            help="Supported file types: PDF, TXT, CSV, DOCX, DOC"
        )
    
    with col2:
        process_now = st.checkbox(
            "Process immediately",
            value=True,
            help="If checked, the document will be processed for RAG immediately after upload"
        )
    
    if uploaded_file and st.button("Upload Document"):
        with st.spinner("Uploading document..."):
            success, message, document_data = upload_document(uploaded_file, process_now)
        
        if success:
            st.success(f"Document uploaded successfully: {document_data.get('original_filename', 'Unknown')}")
            
            # Refresh document list
            refresh_documents()
        else:
            st.error(f"Upload failed: {message}")

def display_documents():
    """Display the list of user's documents"""
    # Initialize or refresh documents if not loaded
    if "documents_loaded" not in st.session_state or not st.session_state.documents_loaded:
        refresh_documents()
        st.session_state.documents_loaded = True
    
    # Check if documents exist
    if not st.session_state.documents:
        st.info("No documents uploaded yet. Upload your first document above.")
        return
    
    # Button to refresh list
    if st.button("🔄 Refresh List"):
        refresh_documents()
    
    # Display documents
    for doc in st.session_state.documents:
        with st.container():
            st.markdown("<div class='document-box'>", unsafe_allow_html=True)
            
            # Document title and basic info
            st.markdown(f"<div class='document-title'>{doc.get('original_filename', 'Unknown')}</div>", unsafe_allow_html=True)
            
            # Format file size
            file_size_str = "Unknown"
            if "file_size" in doc:
                size_kb = doc["file_size"] / 1024
                if size_kb < 1024:
                    file_size_str = f"{size_kb:.1f} KB"
                else:
                    file_size_str = f"{size_kb/1024:.1f} MB"
            
            # Format upload date
            upload_date_str = "Unknown"
            if "upload_date" in doc:
                try:
                    upload_date = datetime.fromisoformat(doc["upload_date"].replace("Z", "+00:00"))
                    upload_date_str = upload_date.strftime("%B %d, %Y at %H:%M")
                except:
                    upload_date_str = doc["upload_date"]
            
            # Display document info
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"<div class='document-info'>Size: {file_size_str}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='document-info'>Type: {doc.get('file_type', 'Unknown')}</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"<div class='document-info'>Uploaded: {upload_date_str}</div>", unsafe_allow_html=True)
                
                # Embedding status
                is_embedded = doc.get("is_embedded", False)
                status_class = "status-embedded" if is_embedded else "status-pending"
                status_text = "Processed" if is_embedded else "Not Processed"
                st.markdown(f"<div class='document-info'>Status: <span class='{status_class}'>{status_text}</span></div>", unsafe_allow_html=True)
            
            # Document actions
            col1, col2 = st.columns(2)
            
            with col1:
                # Process button (only if not already processed)
                if not is_embedded:
                    if st.button("⚙️ Process Document", key=f"process_{doc['_id']}"):
                        with st.spinner("Starting document processing..."):
                            success, message = process_document(str(doc["_id"]))
                            
                        if success:
                            st.success("Document processing started. It may take a few moments to complete.")
                            time.sleep(2)  # Give user time to see the message
                            refresh_documents()
                        else:
                            st.error(f"Processing failed: {message}")
            
            with col2:
                # Delete button
                if st.button("🗑️ Delete", key=f"delete_{doc['_id']}"):
                    if st.session_state.get(f"confirm_delete_{doc['_id']}", False):
                        # Confirmed, delete the document
                        with st.spinner("Deleting document..."):
                            success, message = delete_document(str(doc["_id"]))
                            
                        if success:
                            st.success("Document deleted successfully")
                            time.sleep(1)  # Give user time to see the message
                            refresh_documents()
                        else:
                            st.error(f"Delete failed: {message}")
                        
                        # Reset confirmation state
                        st.session_state[f"confirm_delete_{doc['_id']}"] = False
                    else:
                        # Set confirmation state and show confirmation button
                        st.session_state[f"confirm_delete_{doc['_id']}"] = True
                        st.warning("Click delete again to confirm")
            
            st.markdown("</div>", unsafe_allow_html=True)

def refresh_documents():
    """Fetch and refresh the document list"""
    with st.spinner("Loading documents..."):
        success, message, documents = get_user_documents()
        
    if success:
        set_documents(documents)
    else:
        st.error(f"Failed to load documents: {message}")
        set_documents([])

if __name__ == "__main__":
    main()
