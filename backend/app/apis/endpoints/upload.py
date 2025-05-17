from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
from bson import ObjectId

from app.apis.deps import get_current_active_user, check_token_availability
from app.services.rag_service import (
    save_uploaded_file, 
    process_document, 
    get_user_documents, 
    get_document_by_id, 
    delete_document
)
from app.schemas.document_schemas import DocumentOut, DocumentList, DocumentEmbeddingStatus
from app.services.token_service import deduct_tokens

router = APIRouter()

@router.post("/document", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    process_now: bool = Form(False),
    current_user: Dict = Depends(check_token_availability)
):
    """
    Upload a document for RAG processing
    """
    # Check file size (limit to 10MB for example)
    file_content = await file.read()
    file_size = len(file_content)
    max_size = 10 * 1024 * 1024  # 10MB
    
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 10MB."
        )
    
    # Save file to disk and DB
    document = await save_uploaded_file(
        file_content=file_content,
        original_filename=file.filename,
        user_id=str(current_user["_id"])
    )
    
    # If requested, process the document in the background
    if process_now:
        background_tasks.add_task(
            process_document,
            document_id=str(document["_id"])
        )
        
        # Deduct tokens for processing (simplified token counting)
        estimated_tokens = file_size // 4  # Very rough estimate of tokens
        await deduct_tokens(
            user_id=str(current_user["_id"]),
            tokens=min(estimated_tokens, 1000),  # Cap at 1000 tokens for processing
            operation_type="embedding",
            metadata={"document_id": str(document["_id"])}
        )
    
    return document

@router.post("/process/{document_id}", response_model=DocumentEmbeddingStatus)
async def start_document_processing(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(check_token_availability)
):
    """
    Start processing a previously uploaded document
    """
    # Get document to check ownership
    document = await get_document_by_id(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user owns the document
    if str(document["uploader_id"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to process this document"
        )
    
    # If already embedded, return status
    if document.get("is_embedded", False):
        return {
            "document_id": document_id,
            "is_embedded": True,
            "status": "already_processed",
            "message": "Document is already processed"
        }
    
    # Start processing in background
    background_tasks.add_task(
        process_document,
        document_id=document_id
    )
    
    # Deduct tokens for processing (simplified token counting)
    file_size = document.get("file_size", 0)
    estimated_tokens = file_size // 4  # Very rough estimate of tokens
    await deduct_tokens(
        user_id=str(current_user["_id"]),
        tokens=min(estimated_tokens, 1000),  # Cap at 1000 tokens for processing
        operation_type="embedding",
        metadata={"document_id": document_id}
    )
    
    return {
        "document_id": document_id,
        "is_embedded": False,
        "status": "processing_started",
        "message": "Document processing has been started"
    }

@router.get("/documents", response_model=DocumentList)
async def list_documents(
    skip: int = 0, 
    limit: int = 100,
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Get all documents uploaded by the current user
    """
    total, documents = await get_user_documents(
        user_id=str(current_user["_id"]),
        skip=skip,
        limit=limit
    )
    
    return {"total": total, "documents": documents}

@router.get("/documents/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: str,
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Get a specific document by ID
    """
    document = await get_document_by_id(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user owns the document
    if str(document["uploader_id"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this document"
        )
    
    return document

@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_document(
    document_id: str,
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Delete a document and its vector store
    """
    success = await delete_document(
        document_id=document_id,
        user_id=str(current_user["_id"])
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or could not be deleted"
        )
    
    return None
