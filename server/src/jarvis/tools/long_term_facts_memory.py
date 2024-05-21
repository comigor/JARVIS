import logging
from typing import Type, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import os


_LOGGER = logging.getLogger(__name__)


class LongTermFactsMemoryInput(BaseModel):
    fact: str = Field(description="Fact")


class LongTermFactsMemoryTool(BaseTool):
    name = "long_term_facts_memory"
    description = """Use this when you detect the user input is a fact. Facts will be persisted and should be remembered forever."""
    args_schema: Type[BaseModel] = LongTermFactsMemoryInput

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def _run(self, fact: str) -> str:
        return f"Fact \"{fact}\" was remembered."
