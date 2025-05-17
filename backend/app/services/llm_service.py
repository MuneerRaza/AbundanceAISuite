import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bson import ObjectId
import logging

from langchain_groq import ChatGroq
from langchain.chains import ConversationalRetrievalChain
from langchain.schema import Document
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_community.vectorstores import FAISS
import tiktoken

from app.core.config import settings
from app.db.mongodb_utils import get_collection, CHAT_SESSIONS_COLLECTION, MESSAGES_COLLECTION, DOCUMENTS_COLLECTION
from app.services.token_service import deduct_tokens
from app.services.rag_service import get_embeddings_model

logger = logging.getLogger(__name__)

# Initialize tokenizer for token counting
tokenizer = tiktoken.get_encoding("cl100k_base")  # Using OpenAI's encoding for estimation

def count_tokens(text: str) -> int:
    """Count the number of tokens in a text"""
    return len(tokenizer.encode(text))

def get_llm(model_name: str = "llama3-70b-8192"):
    """
    Get a Groq LLM instance
    """
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name=model_name,
        temperature=0.7,
        max_tokens=2048,
    )

def create_rag_chain(query_texts: List[str], system_prompt: Optional[str] = None):
    """
    Create a RAG chain with retrieved documents
    """
    llm = get_llm()
    
    # Set up system prompt
    if not system_prompt:
        system_prompt = """You are a helpful AI assistant providing accurate and informative answers.
        Answer questions based on the context provided. If you don't know the answer, say so instead of making up information."""
    
    # Create prompt templates
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_prompt)
    
    # Human message template that includes context
    human_template = """Context: {context}
    
    Question: {question}"""
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    
    # Combine prompts
    chat_prompt = ChatPromptTemplate.from_messages([
        system_message_prompt,
        human_message_prompt,
    ])
    
    # Create fake documents from query texts
    documents = [Document(page_content=text) for text in query_texts]
    
    # Return the chain response
    return llm.invoke(chat_prompt.format(context="\n\n".join(query_texts), question=query))

async def get_user_documents_for_retrieval(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all documents uploaded by a user that have been embedded
    """
    documents_collection = await get_collection(DOCUMENTS_COLLECTION)
    cursor = documents_collection.find({
        "uploader_id": ObjectId(user_id),
        "is_embedded": True
    })
    
    return await cursor.to_list(length=100)  # Limit to reasonable amount

async def create_chat_session(user_id: str, title: str) -> str:
    """
    Create a new chat session
    """
    chat_sessions_collection = await get_collection(CHAT_SESSIONS_COLLECTION)
    now = datetime.utcnow()
    
    chat_session = {
        "user_id": ObjectId(user_id),
        "title": title,
        "created_at": now,
        "updated_at": now,
        "is_archived": False
    }
    
    result = await chat_sessions_collection.insert_one(chat_session)
    return str(result.inserted_id)

async def get_chat_sessions(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all chat sessions for a user
    """
    chat_sessions_collection = await get_collection(CHAT_SESSIONS_COLLECTION)
    cursor = chat_sessions_collection.find({"user_id": ObjectId(user_id)})
    cursor.sort("updated_at", -1)  # Most recent first
    
    return await cursor.to_list(length=100)  # Limit to reasonable amount

async def get_chat_messages(chat_session_id: str, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
    """
    Get messages from a chat session with pagination
    """
    messages_collection = await get_collection(MESSAGES_COLLECTION)
    cursor = messages_collection.find({"chat_session_id": ObjectId(chat_session_id)})
    cursor.sort("timestamp", -1).skip(skip).limit(limit)  # Most recent first
    
    return await cursor.to_list(length=limit)

async def process_chat_message(
    user_id: str,
    chat_session_id: str,
    message: str,
    system_prompt: Optional[str] = None,
    use_rag: bool = True
) -> Tuple[str, str, int]:
    """
    Process a chat message, generate a response, and store in database
    
    Args:
        user_id: User ID
        chat_session_id: Chat session ID
        message: User message
        system_prompt: Optional system prompt to customize assistant behavior
        use_rag: Whether to use RAG retrieval
        
    Returns:
        Tuple of (response, message_id, tokens_used)
    """
    # Check if chat session exists
    chat_sessions_collection = await get_collection(CHAT_SESSIONS_COLLECTION)
    chat_session = await chat_sessions_collection.find_one({
        "_id": ObjectId(chat_session_id),
        "user_id": ObjectId(user_id)
    })
    
    if not chat_session:
        raise ValueError("Chat session not found")
    
    # Initialize context for RAG
    context_texts = []
    
    # If using RAG, retrieve relevant documents
    if use_rag:
        embedded_documents = await get_user_documents_for_retrieval(user_id)
        
        if embedded_documents:
            try:
                # Get embeddings model
                embeddings = get_embeddings_model()
                
                # Query each document's vector store
                for doc in embedded_documents:
                    vector_store_path = doc.get("vector_store_id")
                    if vector_store_path and os.path.exists(vector_store_path):
                        vector_store = FAISS.load_local(vector_store_path, embeddings)
                        results = vector_store.similarity_search(message, k=2)
                        
                        # Add retrieved text to context
                        for result in results:
                            context_texts.append(f"From {doc['original_filename']}: {result.page_content}")
            except Exception as e:
                logger.error(f"Error retrieving from vector store: {str(e)}")
                # Continue without RAG results if there's an error
    
    # If no context was found but RAG was requested, add a note
    if use_rag and not context_texts:
        context_texts = ["No relevant information found in your documents."]
    
    # Generate response using the LLM
    try:
        response = create_rag_chain(context_texts, system_prompt)
        response_text = response.content
        
        # Count tokens (estimation)
        message_tokens = count_tokens(message)
        context_tokens = sum(count_tokens(text) for text in context_texts)
        response_tokens = count_tokens(response_text)
        total_tokens = message_tokens + context_tokens + response_tokens
        
        # Store message in database
        messages_collection = await get_collection(MESSAGES_COLLECTION)
        message_data = {
            "user_id": ObjectId(user_id),
            "chat_session_id": ObjectId(chat_session_id),
            "message": message,
            "response": response_text,
            "timestamp": datetime.utcnow(),
            "tokens_used": total_tokens,
            "metadata": {
                "message_tokens": message_tokens,
                "context_tokens": context_tokens,
                "response_tokens": response_tokens,
                "rag_used": use_rag,
                "context_count": len(context_texts)
            }
        }
        
        result = await messages_collection.insert_one(message_data)
        message_id = str(result.inserted_id)
        
        # Update chat session's updated_at timestamp
        await chat_sessions_collection.update_one(
            {"_id": ObjectId(chat_session_id)},
            {"$set": {"updated_at": datetime.utcnow()}}
        )
        
        # Deduct tokens from user's account
        await deduct_tokens(
            user_id=user_id, 
            tokens=total_tokens, 
            operation_type="chat",
            chat_session_id=chat_session_id,
            message_id=message_id
        )
        
        return response_text, message_id, total_tokens
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise
