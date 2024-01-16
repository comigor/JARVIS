from langchain.tools import Tool
from langchain.utilities.google_search import GoogleSearchAPIWrapper

search = GoogleSearchAPIWrapper()

GoogleSearchTool = Tool(
    name="google_search",
    description="Search Google for recent results.",
    func=search.run,
)
