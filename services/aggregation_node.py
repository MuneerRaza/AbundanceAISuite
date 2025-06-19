# project/services/aggregation_node.py

from typing import Dict
from models.state import State

class AggregationNode:
    """
    A node that aggregates results from web search and vector DB retrieval
    into a final, consolidated context string.
    """
    def invoke(self, state: State) -> Dict[str, str]:
        """
        Combines retrieved documents and web search results into a single context string.
        """
        print("---AGGREGATING CONTEXT---")
        retrieved_docs = state.get("retrieved_docs", [])
        web_search_results = state.get("web_search_results", "")
        
        final_context = ""

        if retrieved_docs:
            formatted_docs = "\n\n".join(
                [f"Source: {doc.metadata.get('path', 'N/A')}\nContent: {doc.page_content}" for doc in retrieved_docs]
            )
            final_context += f"---Information from Documents---\n{formatted_docs}\n\n"
        
        if web_search_results:
            final_context += f"---Information from Web Search---\n{web_search_results}\n"
            
        if not final_context:
            final_context = "No relevant information was found to answer the query."
            
        return {"final_context": final_context}