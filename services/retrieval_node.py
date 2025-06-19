from typing import Dict, List
from langchain.schema import Document
from models.state import State
from services.vectordb import advanced_retrieve

class RetrievalNode:
    """
    A node that retrieves documents from the vector database based on the list of tasks.
    """
    def invoke(self, state: State, config: dict) -> Dict[str, List[Document]]:
        """
        Retrieves documents for each task and aggregates them.
        """
        tasks = state.get("tasks", [])
        thread_id = config.get("configurable", {}).get("thread_id")
        
        if not tasks or not thread_id:
            return {"retrieved_docs": []}

        print("---RETRIEVING FROM VECTORDB---")
        all_docs = []
        for task in tasks:
            print(f"Retrieving for task: '{task}'")
            retrieved_docs = advanced_retrieve(query=task, thread_id=thread_id)
            all_docs.extend(retrieved_docs)
        
        # Simple de-duplication based on page content
        unique_docs = {doc.page_content: doc for doc in all_docs}.values()
        
        return {"retrieved_docs": list(unique_docs)}