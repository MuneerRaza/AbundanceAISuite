USER_CHROMA_PATH = "./chroma_db/user"
USER_COLLECTION = "user_attachments"
ADMIN_CHROMA_PATH = "./chroma_db/admin"
ADMIN_COLLECTION = "admin_memory"
IMAGE_STORE_PATH = "extracted_images"
VECTOR_SEARCH_K = 20
CHUNK_SIZE = 1024
CHUNK_OVERLAP = 256

MODEL_ID = "llama3-8b-8192"
UTILS_MODEL_ID = "llama3-8b-8192"

EMBEDDING_MODEL_ID = "BAAI/bge-m3"
# EMBEDDING_MODEL_ID = "nomic-ai/nomic-embed-text-v1.5"
# MODEL_KWARGS = {'device': 'cpu', 'trust_remote_code': True}
# ENCODE_KWARGS = {"normalize_embeddings": True}


SUMMARY_THRESHOLD = 8
MESSAGES_TO_RETAIN = 4

SYSTEM_PROMPT = ("You are an Converstational expert AI assistant. Your task is to answer user's query, provide accurate and concise answers by synthesizing the provided context (conversation summary and recent messages)."
    "Key Directives:"
    "- If context is insufficient to answer accurately, you must ask for clarification instead of inventing information."
    "- Act as if you have a perfect, natural memory. NEVER allude to, mention, or reveal the existence of the 'summary' in your responses. Until user explicitly mentions."
    )