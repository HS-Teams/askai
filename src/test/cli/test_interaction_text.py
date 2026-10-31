import unittest
from unittest.mock import Mock, patch
from askai.cli.interaction_text import translate_request
from askai.cli.agent_interaction import AgentInteraction
from askai.core.agents.elicitation import ELICITATION_METHOD


class InteractionTextTests(unittest.TestCase):
    def test_only_prose_is_translated_without_mutating_request(self):
        original = {'message': 'Allow tool?', 'reason': 'Audio access',
                    'command': 'ffplay song.mp3', 'serverName': 'askai_desktop',
                    'url': 'https://example.com', 'threadId': 'original-id'}
        translated = translate_request(original, lambda text: 'PT: ' + text)
        self.assertEqual(translated['message'], 'PT: Allow tool?')
        self.assertEqual(translated['reason'], 'PT: Audio access')
        for key in ('command', 'serverName', 'url', 'threadId'):
            self.assertEqual(translated[key], original[key])
        self.assertEqual(original['message'], 'Allow tool?')

    def test_mcp_confirmation_passes_through_project_translation(self):
        confirm = Mock(return_value=True)
        translate = Mock(return_value='Permitir reprodução?')
        params = {'serverName': 'askai_desktop', 'mode': 'form', 'message': 'Allow playback?',
                  'requestedSchema': {'type': 'object', 'properties': {}}}
        with patch('sys.stdin.isatty', return_value=True):
            result = AgentInteraction(Mock(), Mock(), confirm=confirm, translate=translate)(ELICITATION_METHOD, params)
        translate.assert_called_once_with('Allow playback?')
        confirm.assert_called_once_with('askai_desktop: Permitir reprodução?')
        self.assertEqual(result, {'action': 'accept', 'content': {}})
