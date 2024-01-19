# Code from https://github.com/KoljaB/Linguflex/blob/main/modules/basic/google_information.py

import logging
from kani import AIFunction, ChatMessage
from typing import List, Any, Dict
from googleapiclient.discovery import build

from .base import BaseAbility

_LOGGER = logging.getLogger(__name__)


class GoogleAbility(BaseAbility):
    def __init__(self, api_key: str, cx_key: str, **kwds):
        super(GoogleAbility, self).__init__('Google', **kwds)
        self.api_key = api_key
        self.google_cx_key = cx_key
        self.search_engine = build('customsearch', 'v1', developerKey=api_key)
        self.k: int = 10
        self.siterestrict: bool = False
        self.num_results: int = 6

    def sys_prompt(self) -> str:
        return ''


    async def chat_history(self) -> List[ChatMessage]:
        return []


    def registered_functions(self) -> List[AIFunction]:
        return [
            AIFunction(
                self.search,
                name='search',
                desc='Retrieves real-time information about current events with google search API from the internet.',
                json_schema={
                    'properties': {
                        'query': {
                            'description': 'Suitable keywords to achieve optimal search engine results which will help answer the query.',
                            'type': 'string',
                        },
                    },
                    'required': ['query'],
                    'type': 'object'
                }
            ),
        ]

    
    def _google_search_results(self, search_term: str, **kwargs: Any) -> List[dict]:
        cse = self.search_engine.cse()
        if self.siterestrict:
            cse = cse.siterestrict()
        res = cse.list(q=search_term, cx=self.google_cx_key, **kwargs).execute()
        return res.get("items", [])

    def run(self, query: str) -> str:
        """Run query through GoogleSearch and parse result."""
        snippets = []
        results = self._google_search_results(query, num=self.k)
        if len(results) == 0:
            return "No good Google Search Result was found"
        for result in results:
            if "snippet" in result:
                snippets.append(result["snippet"])

        return snippets

    def results(self, query: str) -> List[Dict]:
        """Run query through GoogleSearch and return metadata."""
        metadata_results = []
        results = self._google_search_results(query, num=self.num_results)
        if len(results) == 0:
            return [{"Result": "No good Google Search Result was found"}]
        for result in results:
            metadata_result = {
                "title": result["title"],
                "link": result["link"],
            }
            if "snippet" in result:
                metadata_result["snippet"] = result["snippet"]
            metadata_results.append(metadata_result)

        return metadata_results

    async def search(self, query: str = None):
        return {
            "snippets": self.run(query),
            "metadata_results": self.results(query)
        }
