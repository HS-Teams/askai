import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import unittest
from unittest.mock import Mock, patch
from jsonschema import ValidationError

from askai.core.agents.enrollment_tool import register_identities
from askai.core.component.identity_enrollment import EnrollmentFace, EnrollmentPhoto
from askai.core.component.faces.selections import FaceAction, FaceSelection


class EnrollmentToolTests(unittest.TestCase):
    def setUp(self):
        self.workspace = TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.photo = self.root / 'input.jpg'
        self.photo.touch()
        self.face = EnrollmentFace(1, self.root / 'crop.jpg', 'A face', [1.0] * 128)
        self.enrollment = Mock()
        self.enrollment.identities.return_value = []
        self.enrollment.plan.side_effect = lambda selections: [s for s in selections if s.action != FaceAction.SKIP]
        self.enrollment.prepare.return_value = EnrollmentPhoto(self.root / 'preview.jpg', [self.face])
        self.enrollment.save.return_value = [{'name': 'Hugo'}]
        self.camera, self.desktop, self.emit = Mock(), Mock(), Mock()
        self.camera.capture_frame.return_value = str(self.photo)
        self.services = patch('askai.core.agents.enrollment_tool._services', return_value=(
            self.enrollment, self.camera, self.desktop, self.root,
        )).start()
        self.addCleanup(patch.stopall)
        self.cancelled = Event()

    def run_tool(self, arguments, decisions):
        self.interact = Mock(side_effect=decisions)
        reply = register_identities({'threadId': 's', 'turnId': 't', 'arguments': arguments},
                                    self.interact, self.emit, self.cancelled)
        return json.loads(reply['contentItems'][0]['text'])

    def test_camera_consent_then_preview_then_human_names(self):
        timeline = Mock()
        timeline.attach_mock(self.camera.capture_frame, 'capture')
        timeline.attach_mock(self.desktop.open_path, 'preview')
        timeline.attach_mock(self.enrollment.save, 'save')
        result = self.run_tool({}, [{'action': 'accept', 'content': {}},
                                   {'action': 'accept', 'content': {'face_1': 'Hugo', 'action_1': 'new'}}, {'action': 'accept', 'content': {}}])
        self.assertEqual([call[0] for call in timeline.mock_calls], ['capture', 'preview', 'save'])
        self.enrollment.save.assert_called_once_with([FaceSelection(self.face, FaceAction.NEW, 'Hugo')])
        self.assertEqual(result['registered'], [{'name': 'Hugo'}])
        self.assertEqual([call.args[0].kind for call in self.emit.call_args_list],
                         ['camera_started', 'camera_finished', 'tool_progress'])
        self.assertNotIn('target', result)

    def test_files_never_use_camera_and_batch_names_before_save(self):
        result = self.run_tool({'photos': [str(self.photo), str(self.photo)]}, [
            {'action': 'accept', 'content': {}},
            {'action': 'accept', 'content': {'face_1': 'Hugo', 'action_1': 'new'}},
            {'action': 'accept', 'content': {'face_1': 'Maria', 'action_1': 'new'}},
            {'action': 'accept', 'content': {}},
        ])
        self.camera.capture_frame.assert_not_called()
        self.enrollment.save.assert_called_once_with([FaceSelection(self.face, FaceAction.NEW, 'Hugo'), FaceSelection(self.face, FaceAction.NEW, 'Maria')])
        self.assertEqual(result['detected_faces'], 2)

    def test_initial_decline_has_no_services_camera_or_io(self):
        result = self.run_tool({}, [{'action': 'decline'}])
        self.assertEqual(result['status'], 'cancelled')
        self.services.assert_not_called()

    def test_cancel_naming_discards_whole_batch(self):
        result = self.run_tool({'photos': [str(self.photo), str(self.photo)]}, [
            {'action': 'accept', 'content': {}},
            {'action': 'accept', 'content': {'face_1': 'Hugo', 'action_1': 'new'}}, {'action': 'cancel'},
        ])
        self.assertEqual(result['status'], 'cancelled')
        self.enrollment.save.assert_not_called()
        self.assertFalse(list(self.root.glob('identity-enrollment-*')))

    def test_unknown_face_or_model_supplied_names_are_rejected(self):
        with self.assertRaises(ValidationError):
            self.run_tool({'name': 'guessed'}, [])
        self.services.assert_not_called()
        with self.assertRaises(ValidationError):
            self.run_tool({}, [{'action': 'accept', 'content': {}},
                               {'action': 'accept', 'content': {'face_99': 'wrong face'}}])
        self.enrollment.save.assert_not_called()

    def test_no_faces_does_not_open_preview_or_ask_for_names(self):
        self.enrollment.prepare.return_value = EnrollmentPhoto(self.root / 'missing.jpg', [])
        self.enrollment.save.return_value = []
        result = self.run_tool({}, [{'action': 'accept', 'content': {}}])
        self.assertEqual(result['detected_faces'], 0)
        self.desktop.open_path.assert_not_called()
        self.assertEqual(self.interact.call_count, 1)

    def test_preview_error_does_not_save(self):
        self.desktop.open_path.side_effect = RuntimeError('cannot open')
        with self.assertRaises(RuntimeError):
            self.run_tool({}, [{'action': 'accept', 'content': {}}])
        self.enrollment.save.assert_not_called()

    def test_read_only_review_cannot_enroll(self):
        from askai.core.agents.codex import CodexBackend
        transport = Mock()
        transport.receive.side_effect = [
            {'id': 7, 'method': 'item/tool/call', 'params': {'tool': 'register_identities', 'arguments': {}}},
            {'method': 'item/completed', 'params': {'item': {'id': 'a', 'type': 'agentMessage', 'phase': 'final_answer', 'text': 'Done'}}},
            {'method': 'turn/completed', 'params': {'turn': {'id': 't', 'status': 'completed'}}},
        ]
        with patch('askai.core.agents.codex.register_identities') as enroll:
            CodexBackend()._consume(transport, 's', 't', Mock(), Mock(), Event(), allow_tools=False)
        enroll.assert_not_called()
        self.assertFalse(transport.send.call_args.args[0]['result']['success'])

    def test_review_opens_existing_samples_without_camera(self):
        self.enrollment.review.return_value = EnrollmentPhoto(self.root / 'sheet.jpg', [self.face])
        result = self.run_tool({'review': True}, [
            {'action': 'accept', 'content': {}},
            {'action': 'accept', 'content': {'action_1': 'merge', 'face_1': 'Hugo'}},
            {'action': 'accept', 'content': {}},
        ])
        self.camera.capture_frame.assert_not_called()
        self.enrollment.prepare.assert_not_called()
        self.assertEqual(result['status'], 'completed')
        self.enrollment.save.assert_called_once_with([FaceSelection(self.face, FaceAction.MERGE, 'Hugo')])

    def test_final_decline_does_not_save_replace(self):
        self.run_tool({}, [
            {'action': 'accept', 'content': {}},
            {'action': 'accept', 'content': {'action_1': 'replace', 'face_1': 'Hugo'}},
            {'action': 'decline'},
        ])
        self.enrollment.save.assert_not_called()

    def test_blank_action_means_skip_even_if_name_entered(self):
        self.enrollment.save.return_value = []
        result = self.run_tool({}, [
            {'action': 'accept', 'content': {}},
            {'action': 'accept', 'content': {'face_1': 'Hugo'}},
        ])
        self.assertEqual(result['registered'], [])
        self.assertEqual(self.interact.call_count, 2)

    def test_allow_grants_remove_permission_dialogs_but_still_collect_human_choices(self):
        from askai.core.permissions.grants import GrantPolicy
        from askai.core.agents.elicitation import INPUT_FORM_METHOD
        with patch('askai.core.agents.enrollment_tool.grants', GrantPolicy(lambda key: 'allow')):
            result = self.run_tool({}, [
                {'action': 'accept', 'content': {'action_1': 'new', 'face_1': 'Hugo'}},
            ])
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(self.interact.call_count, 1)
        self.assertEqual(self.interact.call_args.args[0], INPUT_FORM_METHOD)
        self.enrollment.save.assert_called_once()

    def test_replace_deny_never_commits_after_human_choices(self):
        from askai.core.permissions.grants import GrantPolicy, GrantDenied
        policy = GrantPolicy(lambda key: 'deny' if key.endswith('identities.replace.local') else 'allow')
        with patch('askai.core.agents.enrollment_tool.grants', policy), self.assertRaises(GrantDenied):
            self.run_tool({}, [
                {'action': 'accept', 'content': {'action_1': 'replace', 'face_1': 'Hugo'}},
            ])
        self.enrollment.save.assert_not_called()
