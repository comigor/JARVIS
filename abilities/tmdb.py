from typing import List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain_core.messages import BaseMessage
from tmdbv3api import TMDb, Movie, Search

from .base import BaseAbility
from .fuckio import async_add_executor_job

class SearchMovieSchema(BaseModel):
    movie_name: str = Field(description='Name of the movie you want to search for')

class SearchMovieTool(BaseTool):
    api_key: str = Field(None)

    def __init__(self, api_key: str, **kwds):
        super(SearchMovieTool, self).__init__(**kwds)
        self.api_key = api_key

    name = 'search_movie_tool'
    description = 'Search for a movie and retrieve information about it'
    args_schema = SearchMovieSchema
    
    async def _arun(self, movie_name: str):
        tmdb = TMDb()
        tmdb.api_key = self.api_key

        # Search for the movie
        search = Search()
        results = await async_add_executor_job(search.movies, term=movie_name)

        if not results:
            return "No results found for the specified movie."

        # Retrieve detailed information about the first result
        movie_id = results[0].id
        movie = Movie()

        watch_providers_filtered = []
        detailed_info_filtered = {}

        watch_providers = await async_add_executor_job(movie.watch_providers, movie_id)
        watch_providers_filtered = list(map(lambda p: p['provider_name'], next(x for x in watch_providers['results'] if x.get('BR')).get('BR')[1].get('flatrate', [])))

        detailed_info = await async_add_executor_job(movie.details, movie_id)
        keys_to_filter = ['id', 'homepage', 'title', 'overview', 'tagline', 'release_date', 'runtime', 'vote_average']
        detailed_info_filtered = dict(zip(keys_to_filter, [detailed_info[k] for k in keys_to_filter]))

        return {
            'watch_providers': watch_providers_filtered,
            'detailed_info': detailed_info_filtered,
        }

    def _run(self, movie_name: str):
        raise NotImplementedError("Synchronous execution is not supported for this tool.")

class MovieSearchAbility(BaseAbility):
    def __init__(self, api_key: str, **kwds):
        super(MovieSearchAbility, self).__init__(**kwds)
        self.api_key = api_key

    def partial_sys_prompt(self) -> str:
        return ""

    async def chat_history(self) -> List[BaseMessage]:
        return []

    def registered_tools(self) -> List[BaseTool]:
        # Return instances of the tools you want to register
        return [SearchMovieTool(self.api_key)]
