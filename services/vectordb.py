import time, hashlib, logging
from typing import List, Dict
from langchain_docling.loader import DoclingLoader, ExportType
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractOcrOptions
from transformers import AutoTokenizer
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors.cross_encoder_rerank import CrossEncoderReranker
from langchain.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain_community.vectorstores.utils import filter_complex_metadata

from config import USER_CHROMA_PATH, USER_COLLECTION, VECTOR_SEARCH_K

logging.basicConfig(
    format="%(asctime)s — %(levelname)s — %(message)s",
    level=logging.INFO
)

# from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
# from dotenv import load_dotenv
# load_dotenv()
# embedder = NVIDIAEmbeddings(model="baai/bge-m3")
embedder = HuggingFaceEmbeddings(model="BAAI/bge-m3")
chroma = Chroma(
    persist_directory=USER_CHROMA_PATH,
    collection_name=USER_COLLECTION,
    embedding_function=embedder
)
tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-m3")
chunker = HybridChunker(tokenizer=tokenizer, merge_peers=True)
reranker_ce = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base")
reranker = CrossEncoderReranker(model=reranker_ce, top_n=3)
pipeline_options = PdfPipelineOptions(
    do_ocr=False,
    do_code_enrichment=True,
    do_formula_enrichment=True,
    ocr_options=TesseractOcrOptions()
)
doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

def file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def load_paths(paths: List[str], thread_id: str) -> List[Dict]:
    metas = []
    for p in paths:
        metas.append({
            "path": p,
            "thread_id": thread_id,
            "file_hash": file_hash(p)
        })
    return metas

def ingest(metas: List[Dict]):
    for m in metas:
        start = time.time()
        exists = chroma._collection.get(
            where={"$and": [{"thread_id": m["thread_id"]}, {"file_hash": m["file_hash"]}]}
        )
        if exists and exists.get("documents"):
            logging.info(f"SKIP {m['path']}: already processed")
            continue

        loader = DoclingLoader(
            file_path=m["path"],
            export_type=ExportType.DOC_CHUNKS,
            chunker=chunker,
        )
        docs: List[Document] = loader.load()

        docs = filter_complex_metadata(docs)
        
        for doc in docs:
            doc.metadata.update(m)
        chroma.add_documents(docs, embeddings=embedder)
        logging.info(f"Ingested {m['path']} → {len(docs)} chunks in {time.time()-start:.2f}s")
    

def advanced_retrieve(query: str, thread_id: str) -> List[Document]:
    docs_for_thread = chroma.get(
        where={"thread_id": thread_id},
        include=["documents", "metadatas"]
    )
    documents = [
        Document(page_content=doc, metadata=meta)
        for doc, meta in zip(docs_for_thread.get("documents", []), docs_for_thread.get("metadatas", []))
    ]

    if not documents:
        logging.warning(f"No documents found for thread_id: {thread_id}")
        return []
    
    bm25_retriever = BM25Retriever.from_documents(documents)
    bm25_retriever.k = VECTOR_SEARCH_K

    dense_retriever = chroma.as_retriever(
        search_kwargs={
            "k": VECTOR_SEARCH_K,
            "filter": {"thread_id": thread_id}
        }
    )

    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, dense_retriever],
        weights=[0.5, 0.5] 
    )

    compression_retriever = ContextualCompressionRetriever(
        base_retriever=ensemble_retriever,
        base_compressor=reranker
    )

    t0 = time.time()
    docs = compression_retriever.invoke(query)
    logging.info(f"Query '{query}' on thread_id '{thread_id}' → {len(docs)} docs in {time.time() - t0:.2f}s")
    return docs




def main(paths: List[str], query: str, thread_id: str):
    metas = load_paths(paths, thread_id)
    ingest(metas)

    # Perform filtered retrieval
    docs = advanced_retrieve(query, thread_id)
    for d in docs:
        print(f"---\n{d.metadata}\n{d.page_content}\n")


if __name__ == "__main__":
    file_list = [r"C:\Users\MuneerRaza\Downloads\CognifootAI_FYP_report_final.pdf"]
    query = "VAE training epochs"
    thread_id = "b"
    main(file_list, query, thread_id)