import logging
from typing import Type, List
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_community.vectorstores import Neo4jVector
from langchain_core.vectorstores import VectorStoreRetriever


_LOGGER = logging.getLogger(__name__)


class SaveLongTermFactsMemoryInput(BaseModel):
    facts: List[str] = Field(description="List of facts")


class SaveLongTermFactsMemoryTool(BaseTool):
    name: str = "save_long_term_facts_memory"
    description: str = """Use this when you detect the user input is one or more facts.
Facts will be persisted and should be remembered forever or until applicable."""
    args_schema: Type[BaseModel] = SaveLongTermFactsMemoryInput

    vectorstore: Neo4jVector = Field()

    def __init__(self, llm: BaseChatModel, **kwds):
        super().__init__(
            **{
                **kwds,
                "vectorstore": Neo4jVector(
                    embedding=OpenAIEmbeddings(), index_name="main"
                ),
            }
        )

    def _run(self, facts: List[str]) -> str:
        self.vectorstore.add_texts(texts=facts)
        return f'Facts "{facts}" were remembered.'


class LoadLongTermFactsMemoryInput(BaseModel):
    query: str = Field(description="The query you want to recall")


class LoadLongTermFactsMemoryTool(BaseTool):
    name: str = "load_long_term_facts_memory"
    description: str = """Use this when you want to recall facts."""
    args_schema: Type[BaseModel] = LoadLongTermFactsMemoryInput

    vectorstore: Neo4jVector = Field()
    retriever: VectorStoreRetriever = Field()

    def __init__(self, llm: BaseChatModel, **kwds):
        retrieval_query = (
            "RETURN node.text AS text, score, {id:elementId(node)} AS metadata"
        )
        vectorstore = Neo4jVector.from_existing_index(
            OpenAIEmbeddings(), index_name="main", retrieval_query=retrieval_query
        )
        retriever = vectorstore.as_retriever()
        super().__init__(
            **{
                **kwds,
                "vectorstore": vectorstore,
                "retriever": retriever,
            }
        )

    def _run(self, query: str) -> str:
        return str(self.retriever.invoke(query))
