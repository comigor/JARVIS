import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure imports from jarvis.tools are possible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from jarvis.tools.homeassistant.toolkit import HomeAssistantToolkit
# Mock the actual tool classes
from jarvis.tools.homeassistant import turn_on_lights, control_entities, get_entity, list_entities, notify_alexa

class TestHomeAssistantToolkit(unittest.TestCase):

    @patch('jarvis.tools.homeassistant.toolkit.HomeAssistantTurnOnLightsTool', spec=turn_on_lights.HomeAssistantTurnOnLightsTool)
    @patch('jarvis.tools.homeassistant.toolkit.HomeAssistantControlEntitiesTool', spec=control_entities.HomeAssistantControlEntitiesTool)
    @patch('jarvis.tools.homeassistant.toolkit.HomeAssistantGetEntityTool', spec=get_entity.HomeAssistantGetEntityTool)
    @patch('jarvis.tools.homeassistant.toolkit.HomeAssistantListAllEntitiesTool', spec=list_entities.HomeAssistantListAllEntitiesTool)
    @patch('jarvis.tools.homeassistant.toolkit.HomeAssistantNotifyAlexaTool', spec=notify_alexa.HomeAssistantNotifyAlexaTool)
    def test_get_tools(self, MockNotifyAlexa, MockListEntities, MockGetEntity, MockControlEntities, MockTurnOnLights):
        
        mock_turn_on_lights_instance = MockTurnOnLights.return_value
        mock_control_entities_instance = MockControlEntities.return_value
        mock_get_entity_instance = MockGetEntity.return_value
        mock_list_entities_instance = MockListEntities.return_value
        mock_notify_alexa_instance = MockNotifyAlexa.return_value
        
        api_key = "test_key"
        base_url = "http://test_url"
        
        toolkit = HomeAssistantToolkit(api_key=api_key, base_url=base_url)
        tools = toolkit.get_tools()

        self.assertEqual(len(tools), 5)

        # Check that tools are instantiated with the correct api_key and base_url
        MockTurnOnLights.assert_called_once_with(base_url=base_url, api_key=api_key)
        MockControlEntities.assert_called_once_with(base_url=base_url, api_key=api_key)
        MockGetEntity.assert_called_once_with(base_url=base_url, api_key=api_key)
        MockListEntities.assert_called_once_with(base_url=base_url, api_key=api_key)
        MockNotifyAlexa.assert_called_once_with(base_url=base_url, api_key=api_key)

        self.assertIn(mock_turn_on_lights_instance, tools)
        self.assertIn(mock_control_entities_instance, tools)
        self.assertIn(mock_get_entity_instance, tools)
        self.assertIn(mock_list_entities_instance, tools)
        self.assertIn(mock_notify_alexa_instance, tools)

if __name__ == '__main__':
    unittest.main()
