from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from askai.core.support.communication import CommunicationBus, ReplyChannel, SESSION_MESSAGES


class CommunicationTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'session' / 'messages.jsonl'
        self.logger = Mock()
        self.bus = CommunicationBus(session_id='current-session', journal=self.path,
                                    recording=lambda: True, logger=self.logger)

    def test_one_message_reaches_screen_session_file_and_log_with_same_identity(self):
        screen = Mock()
        event = self.bus.publish('command.result', {'status': 'completed', 'output': 'Olá'}, screen=screen)
        screen.assert_called_once_with()
        saved = json.loads(self.path.read_text())
        logged = json.loads(self.logger.log.call_args.args[2])
        memory = self.bus.recent()[0]
        self.assertEqual({event['id'], saved['id'], logged['id'], memory['id']}, {event['id']})
        self.assertEqual(saved['session_id'], 'current-session')
        self.assertEqual(saved['payload']['output'], 'Olá')
        self.assertIsNotNone(saved['timestamp'])

    def test_history_off_keeps_screen_and_live_session_without_writing_payloads(self):
        recording = [False]
        self.bus.configure('private', self.path, lambda: recording[0])
        screen = Mock()
        self.bus.publish('reply', {'message': 'Private content'}, screen=screen)
        screen.assert_called_once()
        self.assertEqual(len(self.bus.recent()), 1)
        self.assertFalse(self.path.exists())
        self.logger.log.assert_not_called()
        recording[0] = True
        self.bus.publish('reply', {'message': 'Recorded content'})
        saved = self.path.read_text()
        self.assertNotIn('Private content', saved)
        self.assertIn('Recorded content', saved)

    def test_file_failure_does_not_block_screen_session_or_log(self):
        self.bus.configure('session', Path(self.directory.name), lambda: True)
        screen = Mock()
        event = self.bus.publish('reply', {'message': 'Visible'}, screen=screen)
        screen.assert_called_once()
        self.logger.log.assert_called_once()
        self.assertEqual(event['delivery_errors'][0]['destination'], 'file')
        self.assertEqual(self.bus.recent()[0]['delivery_errors'], event['delivery_errors'])

    def test_screen_failure_does_not_lose_the_recorded_message(self):
        event = self.bus.publish('reply', {'message': 'Saved'}, screen=Mock(side_effect=RuntimeError('UI failed')))
        self.assertTrue(self.path.exists())
        self.assertEqual(event['delivery_errors'], [{'destination': 'screen', 'error_type': 'RuntimeError'}])
        self.assertEqual(self.bus.recent()[0]['payload']['message'], 'Saved')

    def test_logging_failure_does_not_escape_or_block_screen(self):
        self.logger.log.side_effect = OSError('log unavailable')
        self.logger.error.side_effect = OSError('log unavailable')
        screen = Mock()
        event = self.bus.publish('reply', {'message': 'Still visible'}, screen=screen)
        screen.assert_called_once()
        self.assertEqual(event['delivery_errors'], [{'destination': 'log', 'error_type': 'OSError'}])
        self.assertTrue(self.path.exists())

    def test_unavailable_recording_policy_never_causes_payload_persistence(self):
        self.bus.configure('session', self.path, Mock(side_effect=RuntimeError('settings unavailable')))
        screen = Mock()
        event = self.bus.publish('reply', {'message': 'Private'}, screen=screen)
        screen.assert_called_once()
        self.assertFalse(self.path.exists())
        self.logger.log.assert_not_called()
        self.assertEqual(event['delivery_errors'][0]['destination'], 'recording_policy')

    def test_transient_screen_chunks_are_not_duplicated_in_session_or_journal(self):
        screen = Mock()
        self.bus.publish('command.output', {'text': 'Progress'}, screen=screen, remember=False, record=False)
        screen.assert_called_once()
        self.assertEqual(self.bus.recent(), [])
        self.assertFalse(self.path.exists())
        self.logger.log.assert_not_called()

    def test_concurrent_messages_have_complete_unique_journal_lines(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda index: self.bus.publish('test', {'index': index}), range(40)))
        saved = [json.loads(line) for line in self.path.read_text().splitlines()]
        self.assertEqual(len(saved), 40)
        self.assertEqual(len({event['id'] for event in saved}), 40)

    def test_screen_callback_can_wait_for_another_publisher_without_deadlocking(self):
        def screen():
            worker = Thread(target=lambda: self.bus.publish('nested', {'message': 'Worker'}))
            worker.start()
            worker.join(timeout=1)
            self.assertFalse(worker.is_alive())
        event = self.bus.publish('reply', {'message': 'Parent'}, screen=screen)
        self.assertEqual(event['delivery_errors'], [])
        self.assertEqual([entry['kind'] for entry in self.bus.recent()], ['reply', 'nested'])

    def test_session_is_bounded_and_snapshots_do_not_mutate_bus_state(self):
        bus = CommunicationBus()
        for index in range(SESSION_MESSAGES + 2):
            bus.publish('reply', {'index': index})
        snapshot = bus.recent(limit=SESSION_MESSAGES + 10)
        self.assertEqual(len(snapshot), SESSION_MESSAGES)
        self.assertEqual(snapshot[0]['payload']['index'], 2)
        snapshot[-1]['payload']['index'] = -1
        self.assertNotEqual(bus.recent()[-1]['payload']['index'], -1)
        self.assertEqual(bus.recent(limit=0), [])

    def test_existing_reply_adapter_routes_screen_and_shared_message(self):
        channel = Mock()
        reply = SimpleNamespace(message='Final answer', is_success=True, is_final=True)
        with patch('askai.core.support.communication.communication', self.bus):
            ReplyChannel(channel).emit(reply=reply, erase_last=False)
        channel.emit.assert_called_once_with(reply=reply, erase_last=False)
        self.assertEqual(self.bus.recent()[0]['payload']['message'], 'Final answer')
