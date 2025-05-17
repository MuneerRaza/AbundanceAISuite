import requests
import streamlit as st
from typing import Dict, Any, List, Optional, Tuple
import json

from utils.state_management import get_api_url, get_auth_headers, logout_user

# Error handling wrapper
def handle_api_error(response):
    """Handle API errors and return appropriate message"""
    try:
        if response.status_code == 401:
            # Unauthorized - token expired or invalid
            logout_user()
            return False, "Your session has expired. Please log in again."
        elif response.status_code == 403:
            # Forbidden - not enough permissions
            return False, "You don't have permission to perform this action."
        elif response.status_code == 404:
            # Not found
            return False, "The requested resource was not found."
        elif response.status_code >= 400:
            # Other client/server errors
            error_detail = "An error occurred."
            try:
                error_data = response.json()
                if "detail" in error_data:
                    error_detail = error_data["detail"]
            except:
                pass
            return False, f"Error: {error_detail}"
        
        # Successful response
        return True, None
    except Exception as e:
        return False, f"An unexpected error occurred: {str(e)}"

# Authentication API
def login_user(email: str, password: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Authenticate user and get access token
    
    Returns:
        Tuple of (success, message, data)
    """
    try:
        login_url = f"{get_api_url()}/auth/login"
        response = requests.post(
            login_url,
            data={
                "username": email,  # OAuth2 uses username field
                "password": password
            }
        )
        
        success, error_msg = handle_api_error(response)
        if not success:
            return False, error_msg, {}
        
        # Get token from response
        data = response.json()
        return True, "Login successful", data
        
    except Exception as e:
        return False, f"Login failed: {str(e)}", {}

def register_user(email: str, password: str, full_name: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Register a new user
    
    Returns:
        Tuple of (success, message, data)
    """
    try:
        signup_url = f"{get_api_url()}/auth/signup"
        response = requests.post(
            signup_url,
            json={
                "email": email,
                "password": password,
                "full_name": full_name
            }
        )
        
        success, error_msg = handle_api_error(response)
        if not success:
            return False, error_msg, {}
        
        # Get created user from response
        data = response.json()
        return True, "Registration successful", data
        
    except Exception as e:
        return False, f"Registration failed: {str(e)}", {}

def get_user_info() -> Tuple[bool, Dict[str, Any]]:
    """
    Get current user profile information
    
    Returns:
        Tuple of (success, user_data)
    """
    try:
        user_url = f"{get_api_url()}/users/me"
        response = requests.get(
            user_url,
            headers=get_auth_headers()
        )
        
        success, error_msg = handle_api_error(response)
        if not success:
            return False, {}
        
        user_data = response.json()
        return True, user_data
        
    except Exception as e:
        return False, {}

def update_user_profile(update_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Update user profile
    
    Returns:
        Tuple of (success, message, updated_user_data)
    """
    try:
        update_url = f"{get_api_url()}/users/me"
        response = requests.put(
            update_url,
            json=update_data,
            headers=get_auth_headers()
        )
        
        success, error_msg = handle_api_error(response)
        if not success:
            return False, error_msg, {}
        
        updated_user = response.json()
        return True, "Profile updated successfully", updated_user
        
    except Exception as e:
        return False, f"Update failed: {str(e)}", {}

# Chat API
def create_chat_session(title: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Create a new chat session
    
    Returns:
        Tuple of (success, message, chat_session)
    """
    try:
        create_url = f"{get_api_url()}/chat/sessions"
        payload = {}
        if title: # Only include title if provided
            payload["title"] = title

        response = requests.post(
            create_url,
            json=payload, # Use the payload dictionary
            headers=get_auth_headers()
        )
        
        success, error_msg = handle_api_error(response)
        if not success:
            return False, error_msg, {}
        
        chat_session = response.json()
        return True, "Chat session created", chat_session
        
    except Exception as e:
        return False, f"Failed to create chat: {str(e)}", {}

def get_chat_sessions() -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Get all chat sessions for current user
    
    Returns:
        Tuple of (success, message, chat_sessions)
    """
    try:
        sessions_url = f"{get_api_url()}/chat/sessions"
        response = requests.get(
            sessions_url,
            headers=get_auth_headers()
        )
        
        success, error_msg = handle_api_error(response)
        if not success:
            return False, error_msg, []
        
        chat_sessions = response.json()
        return True, "", chat_sessions
        
    except Exception as e:
        return False, f"Failed to load chat sessions: {str(e)}", []

def get_chat_history(chat_id: str, limit: int = 50, skip: int = 0) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Get messages from a chat session
    
    Returns:
        Tuple of (success, message, messages)
    """
    try:
        history_url = f"{get_api_url()}/chat/sessions/{chat_id}/messages?limit={limit}&skip={skip}"
        response = requests.get(
            history_url,
            headers=get_auth_headers()
        )
        
        success, error_msg = handle_api_error(response)
        if not success:
            return False, error_msg, []
        
        messages = response.json()
        return True, "", messages
        
    except Exception as e:
        return False, f"Failed to load chat history: {str(e)}", []

def send_chat_message(
    chat_id: str, 
    message: str, 
    system_prompt: Optional[str] = None,
    use_rag: bool = True
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Send a message and get AI response
    
    Returns:
        Tuple of (success, message, response_data)
    """
    try:
        completion_url = f"{get_api_url()}/chat/completion"
        payload = {
            "chat_session_id": chat_id,
            "message": message,
            "use_rag": use_rag
        }
        
        if system_prompt:
            payload["system_prompt"] = system_prompt
        
        response = requests.post(
            completion_url,
            json=payload,
            headers=get_auth_headers()
        )
        
        success, error_msg = handle_api_error(response)
        if not success:
            return False, error_msg, {}
        
        response_data = response.json()
        return True, "", response_data
        
    except Exception as e:
        return False, f"Failed to send message: {str(e)}", {}

# Document API
def upload_document(file, process_now: bool = False) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Upload a document for RAG
    
    Returns:
        Tuple of (success, message, document_data)
    """
    try:
        upload_url = f"{get_api_url()}/upload/document"
        
        files = {"file": (file.name, file, file.type)}
        data = {"process_now": "true" if process_now else "false"}
        
        response = requests.post(
            upload_url,
            files=files,
            data=data,
            headers=get_auth_headers()
        )
        
        success, error_msg = handle_api_error(response)
        if not success:
            return False, error_msg, {}
        
        document_data = response.json()
        return True, "Document uploaded successfully", document_data
        
    except Exception as e:
        return False, f"Upload failed: {str(e)}", {}

def get_user_documents(skip: int = 0, limit: int = 100) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Get all documents for current user
    
    Returns:
        Tuple of (success, message, documents)
    """
    try:
        documents_url = f"{get_api_url()}/upload/documents?skip={skip}&limit={limit}"
        response = requests.get(
            documents_url,
            headers=get_auth_headers()
        )
        
        success, error_msg = handle_api_error(response)
        if not success:
            return False, error_msg, []
        
        documents_data = response.json()
        return True, "", documents_data.get("documents", [])
        
    except Exception as e:
        return False, f"Failed to load documents: {str(e)}", []

def process_document(document_id: str) -> Tuple[bool, str]:
    """
    Start processing a document for RAG
    
    Returns:
        Tuple of (success, message)
    """
    try:
        process_url = f"{get_api_url()}/upload/process/{document_id}"
        response = requests.post(
            process_url,
            headers=get_auth_headers()
        )
        
        success, error_msg = handle_api_error(response)
        if not success:
            return False, error_msg
        
        return True, "Document processing started"
        
    except Exception as e:
        return False, f"Processing failed: {str(e)}"

def delete_document(document_id: str) -> Tuple[bool, str]:
    """
    Delete a document
    
    Returns:
        Tuple of (success, message)
    """
    try:
        delete_url = f"{get_api_url()}/upload/documents/{document_id}"
        response = requests.delete(
            delete_url,
            headers=get_auth_headers()
        )
        
        success, error_msg = handle_api_error(response)
        if not success:
            return False, error_msg
        
        return True, "Document deleted successfully"
        
    except Exception as e:
        return False, f"Delete failed: {str(e)}"
