import logging
from typing import Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.language_models import BaseChatModel
from langchain_core.documents import Document
from langchain.graphs.neo4j_graph import Neo4jGraph
from langchain.chains.graph_qa.cypher_utils import CypherQueryCorrector, Schema


_LOGGER = logging.getLogger(__name__)


class SaveLongTermFactsMemoryInput(BaseModel):
    facts: str = Field(description="Facts")


class SaveLongTermFactsMemoryTool(BaseTool):
    name = "save_long_term_facts_memory"
    description = """Use this when you detect the user input is one or more facts.
Facts will be persisted and should be remembered forever or until applicable."""
    args_schema: Type[BaseModel] = SaveLongTermFactsMemoryInput

    llm_transformer: LLMGraphTransformer = Field()
    graph: Neo4jGraph = Field()

    def __init__(self, llm: BaseChatModel, **kwds):
        super().__init__(**{
            **kwds,
            "llm_transformer": LLMGraphTransformer(llm=llm),
            "graph": Neo4jGraph(),
        })

    def _run(self, facts: str) -> str:
        graph_documents = self.llm_transformer.convert_to_graph_documents([Document(page_content=facts)])
        self.graph.add_graph_documents(
            graph_documents, 
            baseEntityLabel=True, 
            include_source=True,
        )

        print(f"Nodes:{graph_documents[0].nodes}")
        print(f"Relationships:{graph_documents[0].relationships}")
        return f"Facts \"{facts}\" were remembered."


class LoadLongTermFactsMemoryInput(BaseModel):
    query: str = Field(description="The query you want to recall")


class LoadLongTermFactsMemoryTool(BaseTool):
    name = "load_long_term_facts_memory"
    description = """Use this when you want to recall facts."""
    args_schema: Type[BaseModel] = LoadLongTermFactsMemoryInput

    llm: BaseChatModel = Field()
    graph: Neo4jGraph = Field()

    def __init__(self, llm: BaseChatModel, **kwds):
        super().__init__(**{
            **kwds,
            "llm": llm,
            "graph": Neo4jGraph(),
        })


    def _run(self, query: str) -> str:
        self.graph.refresh_schema()
        corrector_schema = [
            Schema(el["start"], el["type"], el["end"])
            for el in self.graph.structured_schema.get("relationships", [])
        ]
        corrector = CypherQueryCorrector(corrector_schema)

        cypher = self.llm.invoke(f"""Given an input question, convert it to a Cypher query. No pre-amble. Do not format code.
Based on the Neo4j graph schema below, write a Cypher query that would answer the user's question:
{self.graph.get_schema}

Question: {query}
Cypher query:""", stop=["\nCypherResult:"])

        context = self.graph.query(corrector(str(cypher.content)))
        return str(context)
