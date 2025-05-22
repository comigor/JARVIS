import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json

# Ensure imports from jarvis.tools are possible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from jarvis.tools.homeassistant.control_entities import HomeAssistantControlEntitiesTool, CommandEnum
from jarvis.tools.homeassistant.get_entity import HomeAssistantGetEntityTool
from jarvis.tools.homeassistant.list_entities import HomeAssistantListAllEntitiesTool
from jarvis.tools.homeassistant.notify_alexa import HomeAssistantNotifyAlexaTool
from jarvis.tools.homeassistant.turn_on_lights import HomeAssistantTurnOnLightsTool

class TestHomeAssistantTools(unittest.TestCase):
    
    def setUp(self):
        self.mock_client = MagicMock(spec=sys.modules.get('httpx.Client', MagicMock())) # More robust mock
        
        # Common setup for tools
        self.base_url = "http://fakehass:8123"
        self.api_key = "test_api_key"

    @patch('httpx.Client')
    def test_control_entities_tool(self, MockHttpxClient):
        MockHttpxClient.return_value = self.mock_client
        tool = HomeAssistantControlEntitiesTool(api_key=self.api_key, base_url=self.base_url)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"status": "ok"}]
        self.mock_client.post.return_value = mock_response

        entities = ["light.living_room", "switch.fan"]
        command = CommandEnum.turn_on
        
        result = tool._run(command=command, entities=entities)
        
        self.assertIn("ok", result)
        self.mock_client.post.assert_called_once_with(
            f"{self.base_url}/api/services/homeassistant/{command.value}",
            headers=tool.headers,
            json={"entity_id": entities}
        )

    @patch('httpx.Client')
    def test_get_entity_tool(self, MockHttpxClient):
        MockHttpxClient.return_value = self.mock_client
        tool = HomeAssistantGetEntityTool(api_key=self.api_key, base_url=self.base_url)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"entity_id": "sensor.temperature", "state": "25"}
        self.mock_client.get.return_value = mock_response
        
        entity_id = "sensor.temperature"
        result = tool._run(entity=entity_id)
        
        self.assertIn("sensor.temperature", result)
        self.assertIn("25", result)
        self.mock_client.get.assert_called_once_with(
            f"{self.base_url}/api/states/{entity_id}",
            headers=tool.headers
        )

    @patch('httpx.Client')
    def test_list_all_entities_tool(self, MockHttpxClient):
        MockHttpxClient.return_value = self.mock_client
        tool = HomeAssistantListAllEntitiesTool(api_key=self.api_key, base_url=self.base_url)

        mock_response_data = [
            {"entity_id": "light.kitchen", "state": "on"},
            {"entity_id": "switch.living_room_fan", "state": "off"},
            {"entity_id": "sensor.bedroom_temp", "state": "22"},
            {"entity_id": "other.device", "state": "unknown"} # Should be filtered out
        ]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        self.mock_client.get.return_value = mock_response
        
        result = tool._run()
        
        expected_filtered_data = [
            {"entity_id": "light.kitchen", "entity_type": "light", "state": "on"},
            {"entity_id": "switch.living_room_fan", "entity_type": "switch", "state": "off"},
            {"entity_id": "sensor.bedroom_temp", "entity_type": "sensor", "state": "22"},
        ]
        self.assertEqual(json.loads(result), expected_filtered_data)
        self.mock_client.get.assert_called_once_with(
            f"{self.base_url}/api/states",
            headers=tool.headers
        )

    @patch('httpx.Client')
    def test_notify_alexa_tool(self, MockHttpxClient):
        MockHttpxClient.return_value = self.mock_client
        tool = HomeAssistantNotifyAlexaTool(api_key=self.api_key, base_url=self.base_url)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"status": "message_sent"}]
        # The tool makes two POST calls, first for sound, then for notification
        self.mock_client.post.return_value = mock_response
        
        message = "Hello from Jarvis"
        target_device = "media_player.echo_living_room"
        
        result = tool._run(message=message, target=target_device)
        
        self.assertIn("message_sent", result)
        self.assertEqual(self.mock_client.post.call_count, 2)
        
        # Check the call for playing media (sound)
        self.mock_client.post.assert_any_call(
            f"{self.base_url}/api/services/media_player/play_media",
            headers=tool.headers,
            json={
                "entity_id": target_device,
                "media_content_type": "sound",
                "media_content_id": "bell_02",
            }
        )
        # Check the call for sending notification
        self.mock_client.post.assert_any_call(
            f"{self.base_url}/api/services/notify/alexa_media",
            headers=tool.headers,
            json={
                "message": message,
                "target": target_device,
            }
        )

    @patch('httpx.Client')
    def test_turn_on_lights_tool(self, MockHttpxClient):
        MockHttpxClient.return_value = self.mock_client
        tool = HomeAssistantTurnOnLightsTool(api_key=self.api_key, base_url=self.base_url)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"status": "lights_on"}]
        self.mock_client.post.return_value = mock_response

        entities = ["light.bedroom"]
        brightness_pct = 80
        
        result = tool._run(entities=entities, brightness_pct=brightness_pct)
        
        self.assertIn("lights_on", result)
        self.mock_client.post.assert_called_once_with(
            f"{self.base_url}/api/services/light/turn_on",
            headers=tool.headers,
            json={
                "entity_id": entities,
                "brightness_pct": brightness_pct
            }
        )

if __name__ == '__main__':
    unittest.main()
