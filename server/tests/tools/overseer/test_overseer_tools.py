import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json

# Ensure imports from jarvis.tools are possible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from jarvis.tools.overseer.request import OverseerDownloadTool, MediaType
from jarvis.tools.overseer.search import OverseerSearchTool

class TestOverseerTools(unittest.TestCase):

    def setUp(self):
        self.mock_client = MagicMock(spec=sys.modules.get('httpx.Client', MagicMock()))
        self.base_url = "http://fakeoverseer"
        self.api_key = "test_overseer_api_key"

    @patch('httpx.Client')
    def test_overseer_download_tool_movie(self, MockHttpxClient):
        MockHttpxClient.return_value = self.mock_client
        tool = OverseerDownloadTool(api_key=self.api_key, base_url=self.base_url)

        mock_response = MagicMock()
        mock_response.status_code = 201
        self.mock_client.post.return_value = mock_response

        media_id = 123
        media_type = MediaType.movie
        
        result = tool._run(media_id=media_id, media_type=media_type)
        
        self.assertEqual(result, "OK, it will be downloaded")
        self.mock_client.post.assert_called_once_with(
            f"{self.base_url}/api/v1/request",
            headers=tool.headers,
            json={"mediaId": media_id, "mediaType": media_type.value}
        )

    @patch('httpx.Client')
    def test_overseer_download_tool_tv(self, MockHttpxClient):
        MockHttpxClient.return_value = self.mock_client
        tool = OverseerDownloadTool(api_key=self.api_key, base_url=self.base_url)

        mock_response = MagicMock()
        mock_response.status_code = 201
        self.mock_client.post.return_value = mock_response

        media_id = 456
        media_type = MediaType.tv
        
        result = tool._run(media_id=media_id, media_type=media_type)
        
        self.assertEqual(result, "OK, it will be downloaded")
        self.mock_client.post.assert_called_once_with(
            f"{self.base_url}/api/v1/request",
            headers=tool.headers,
            json={"mediaId": media_id, "mediaType": media_type.value, "seasons": [1]}
        )

    @patch('httpx.Client')
    def test_overseer_download_tool_error(self, MockHttpxClient):
        MockHttpxClient.return_value = self.mock_client
        tool = OverseerDownloadTool(api_key=self.api_key, base_url=self.base_url)

        mock_response = MagicMock()
        mock_response.status_code = 500
        self.mock_client.post.return_value = mock_response
        
        result = tool._run(media_id=123, media_type=MediaType.movie)
        self.assertEqual(result, "Sorry, I can't do that (got error 500)")


    @patch('httpx.Client')
    def test_overseer_search_tool(self, MockHttpxClient):
        MockHttpxClient.return_value = self.mock_client
        tool = OverseerSearchTool(api_key=self.api_key, base_url=self.base_url)

        mock_api_response_data = {
            "results": [
                {"id": 1, "title": "Test Movie 1", "overview": "Overview 1", "popularity": 10, "releaseDate": "2023-01-01", "voteAverage": 7.5},
                {"id": 2, "title": "Test Show 2", "overview": "Overview 2", "popularity": 12, "releaseDate": "2023-02-01", "voteAverage": 8.0},
            ]
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response_data
        self.mock_client.get.return_value = mock_response
        
        query = "Test Query"
        result = tool._run(query=query)
        
        expected_filtered_data = [
            {"id": 1, "title": "Test Movie 1", "overview": "Overview 1", "popularity": 10, "releaseDate": "2023-01-01", "voteAverage": 7.5},
            {"id": 2, "title": "Test Show 2", "overview": "Overview 2", "popularity": 12, "releaseDate": "2023-02-01", "voteAverage": 8.0},
        ]
        self.assertEqual(json.loads(result), expected_filtered_data)
        self.mock_client.get.assert_called_once_with(
            f"{self.base_url}/api/v1/search?query={query}&page=1&language=en",
            headers=tool.headers
        )

if __name__ == '__main__':
    unittest.main()
