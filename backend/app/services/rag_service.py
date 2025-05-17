import os
import shutil
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from bson import ObjectId
import mimetypes
import logging

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import (
    PyPDFLoader, 
    TextLoader, 
    CSVLoader, 
    UnstructuredWordDocumentLoader
)

from app.core.config import settings
from app.db.mongodb_utils import get_collection, DOCUMENTS_COLLECTION

logger = logging.getLogger(__name__)

# Supported file types and their loaders
DOCUMENT_LOADERS = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".csv": CSVLoader,
    ".docx": UnstructuredWordDocumentLoader,
    ".doc": UnstructuredWordDocumentLoader,
}

# Initialize embeddings model
def get_embeddings_model():
    """
    Get the embeddings model
    For simplicity, using a local HuggingFace model
    """
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2"
    )

async def save_uploaded_file(
    file_content: bytes,
    original_filename: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Save an uploaded file to disk and record in database
    
    Args:
        file_content: File bytes
        original_filename: Original filename
        user_id: User ID who uploaded the file
        
    Returns:
        Dict containing document info
    """
    # Generate a unique filename
    file_extension = os.path.splitext(original_filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Create user folder if it doesn't exist
    user_folder = os.path.join(settings.UPLOADED_FILES_DIR, user_id)
    os.makedirs(user_folder, exist_ok=True)
    
    # Full path for saving
    file_path = os.path.join(user_folder, unique_filename)
    
    # Save file to disk
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Get file size
    file_size = len(file_content)
    
    # Get MIME type
    mime_type, _ = mimetypes.guess_type(original_filename)
    file_type = mime_type or f"application/{file_extension[1:]}"
    
    # Create document record in database
    document_data = {
        "filename": unique_filename,
        "original_filename": original_filename,
        "uploader_id": ObjectId(user_id),
        "upload_date": datetime.utcnow(),
        "file_size": file_size,
        "file_type": file_type,
        "local_path": file_path,
        "is_embedded": False,
        "metadata": {
            "extension": file_extension,
        }
    }
    
    documents_collection = await get_collection(DOCUMENTS_COLLECTION)
    result = await documents_collection.insert_one(document_data)
    document_data["_id"] = result.inserted_id
    
    return document_data

async def process_document(document_id: str) -> Tuple[bool, str]:
    """
    Process a document: load, split, embed, and store in vector database
    
    Args:
        document_id: Document ID to process
        
    Returns:
        Tuple of (success, message)
    """
    # Get document info
    documents_collection = await get_collection(DOCUMENTS_COLLECTION)
    document = await documents_collection.find_one({"_id": ObjectId(document_id)})
    
    if not document:
        return False, "Document not found"
    
    try:
        # Get file path and extension
        file_path = document["local_path"]
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Check if we support this file type
        if file_extension not in DOCUMENT_LOADERS:
            return False, f"Unsupported file type: {file_extension}"
        
        # Load document
        loader_class = DOCUMENT_LOADERS[file_extension]
        loader = loader_class(file_path)
        documents = loader.load()
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len,
        )
        splits = text_splitter.split_documents(documents)
        
        if len(splits) == 0:
            return False, "No content extracted from document"
        
        # Create vector store directory
        user_id = str(document["uploader_id"])
        vector_dir = os.path.join(
            settings.VECTOR_INDEXES_DIR, 
            user_id,
            str(document["_id"])
        )
        os.makedirs(os.path.dirname(vector_dir), exist_ok=True)
        
        # Get embeddings model and create vector store
        embeddings = get_embeddings_model()
        vector_store = FAISS.from_documents(splits, embeddings)
        
        # Save vector store
        vector_store.save_local(vector_dir)
        
        # Update document in database
        await documents_collection.update_one(
            {"_id": document["_id"]},
            {
                "$set": {
                    "is_embedded": True,
                    "vector_store_id": vector_dir,
                    "metadata.page_count": len(splits),
                    "metadata.processing_completed": datetime.utcnow()
                }
            }
        )
        
        return True, f"Document processed successfully with {len(splits)} chunks"
    
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        return False, f"Error processing document: {str(e)}"

async def get_user_documents(user_id: str, skip: int = 0, limit: int = 100) -> Tuple[int, List[Dict]]:
    """
    Get documents uploaded by a user
    
    Args:
        user_id: User ID
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        
    Returns:
        Tuple of (total count, documents list)
    """
    documents_collection = await get_collection(DOCUMENTS_COLLECTION)
    
    # Count total documents
    total = await documents_collection.count_documents({"uploader_id": ObjectId(user_id)})
    
    # Get documents with pagination
    cursor = documents_collection.find({"uploader_id": ObjectId(user_id)})
    cursor.sort("upload_date", -1).skip(skip).limit(limit)
    
    documents = await cursor.to_list(length=limit)
    return total, documents

async def get_document_by_id(document_id: str) -> Optional[Dict]:
    """
    Get a document by ID
    
    Args:
        document_id: Document ID
        
    Returns:
        Document data or None if not found
    """
    documents_collection = await get_collection(DOCUMENTS_COLLECTION)
    return await documents_collection.find_one({"_id": ObjectId(document_id)})

async def delete_document(document_id: str, user_id: str) -> bool:
    """
    Delete a document and its vector store
    
    Args:
        document_id: Document ID
        user_id: User ID (for authorization check)
        
    Returns:
        True if document was deleted, False otherwise
    """
    documents_collection = await get_collection(DOCUMENTS_COLLECTION)
    document = await documents_collection.find_one({"_id": ObjectId(document_id)})
    
    if not document:
        return False
    
    # Check if user owns this document
    if str(document["uploader_id"]) != user_id:
        return False
    
    try:
        # Delete from filesystem
        if os.path.exists(document["local_path"]):
            os.remove(document["local_path"])
        
        # Delete vector store if it exists
        if document.get("vector_store_id") and os.path.exists(document["vector_store_id"]):
            shutil.rmtree(document["vector_store_id"])
        
        # Delete from database
        await documents_collection.delete_one({"_id": ObjectId(document_id)})
        return True
    
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        return False
