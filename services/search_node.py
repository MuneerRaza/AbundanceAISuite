from typingimport Dict
from langchain_community.tools.tavily_search import TavilySearchResults

from models.state import State

class SearchNode:
    """
    A node that performs a web search using Tavily based on the rewritten query.
    """
    def __init__(self):
        self.search_tool = TavilySearchResults(max_results=3)

    def invoke(self, state: State) -> Dict[str, str]:
        """
        Performs a web search and returns the results.
        """
        rewritten_query = state.get("rewritten_query", "")
        if not rewritten_query:
            return {"web_search_results": ""}
            
        print("---SEARCHING THE WEB---")
        try:
            results = self.search_tool.invoke(rewritten_query)
            # Format the results into a single string for the context
            formatted_results = "\n\n".join([f"URL: {res['url']}\nContent: {res['content']}" for res in results])
            return {"web_search_results": formatted_results}
        except Exception as e:
            print(f"Error during Tavily search: {e}")
            return {"web_search_results": "Error performing web search."}