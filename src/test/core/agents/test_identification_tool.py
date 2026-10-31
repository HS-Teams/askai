import json
import sys
import unittest
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock, patch
from askai.core.agents.identification_tool import identify_camera


class IdentificationTests(unittest.TestCase):
    def run_tool(self, action='accept', arguments=None):
        camera, models, index = Mock(), Mock(), Mock()
        camera.capture_frame.return_value = '/photos/captured.jpg'
        models.detect.return_value = [SimpleNamespace(vector=[1.0] * 128)]
        index.match.return_value = [{'face': 1, 'status': 'matched', 'name': 'Hugo', 'similarity': 0.9}]
        interaction = Mock(return_value={'action': action, 'content': {}})
        with patch.dict(sys.modules, {
            'askai.core.askai_configs': Mock(configs=SimpleNamespace(identity_similarity_threshold=0.363)),
            'askai.core.component.multimedia.camera': Mock(camera=camera),
        }), patch('askai.core.component.faces.service.face_services', return_value=(models, index, {})), patch(
            'askai.core.agents.identification_tool.cv2.imread'
        ):
            result = identify_camera({'threadId': 's', 'turnId': 't', 'arguments': arguments or {}},
                                     interaction, Mock(), Event())
        return json.loads(result['contentItems'][0]['text']), camera, index, interaction

    def test_recognition_returns_only_results_not_paths_or_vectors(self):
        result, _, index, _ = self.run_tool()
        self.assertEqual(result['faces'][0]['name'], 'Hugo')
        index.match.assert_called_once_with([[1.0] * 128], 0.363)
        for field in ('target', 'uri', 'vector'):
            self.assertNotIn(field, json.dumps(result))

    def test_threshold_override(self):
        _, _, index, _ = self.run_tool(arguments={'threshold': 0.5})
        self.assertEqual(index.match.call_args.args[1], 0.5)

    def test_declined_capture_never_compares(self):
        for action in ('decline', 'cancel'):
            result, camera, index, _ = self.run_tool(action=action)
            self.assertEqual(result['status'], 'cancelled')
            camera.capture_frame.assert_not_called()
            index.match.assert_not_called()

    def test_bad_threshold_rejected_before_consent(self):
        for threshold in (-2, 2, float('nan'), float('inf'), True, '0.4'):
            with self.subTest(threshold=threshold), self.assertRaises(ValueError):
                self.run_tool(arguments={'threshold': threshold})
