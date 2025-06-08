import os
import logging

USER_CHROMA_PATH = "./chroma_db/user"
USER_COLLECTION = "user_long_memory"
ADMIN_CHROMA_PATH = "./chroma_db/admin"
ADMIN_COLLECTION = "admin_memory"
ATTACHMENT_COLLECTION = "attachments"
ATTACHMENT_CHROMA_PATH = "./chroma_db/attachments"
VECTOR_SEARCH_K = 5
CHUNK_SIZE = 1024
CHUNK_OVERLAP = 256

MODEL_ID = "llama3-8b-8192"
SUMMARY_MODEL_ID = "llama3-8b-8192"

# EMBEDDING_MODEL_ID = "BAAI/bge-m3"
EMBEDDING_MODEL_ID = "nomic-ai/nomic-embed-text-v1.5"
MODEL_KWARGS = {'device': 'cpu', 'trust_remote_code': True}
ENCODE_KWARGS = {"normalize_embeddings": True}


SUMMARY_THRESHOLD = 8
MESSAGES_TO_RETAIN = 4