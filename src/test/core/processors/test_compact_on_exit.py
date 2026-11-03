import unittest
from unittest.mock import Mock, patch
from askai.core.processors.taius import TaiusProcessor


class CompactOnExitTests(unittest.TestCase):
    def setUp(self):
        self.configs = Mock(is_keep_context=True, compact_on_exit=True)
        self.events = Mock()
        self.messages = Mock()
        self.messages.t.side_effect = lambda text: text
        modules = patch.dict('sys.modules', {
            'askai.core.askai_configs': Mock(configs=self.configs),
            'askai.core.askai_events': Mock(events=self.events),
            'askai.core.askai_messages': Mock(msg=self.messages),
        })
        modules.start()
        self.addCleanup(modules.stop)
        self.processor = TaiusProcessor()
        self.processor._orchestrator = Mock()
        self.processor._orchestrator.cancelled.is_set.return_value = False

    def test_normal_exit_compacts_only_once(self):
        self.processor.compact_on_exit()
        self.processor.compact_on_exit()
        self.processor._orchestrator.compact_session.assert_called_once()
        self.assertTrue(self.processor._orchestrator.compact_session.call_args.kwargs['wait'])

    def test_disabled_and_interrupted_exit_do_not_compact(self):
        for enabled, cancelled in ((False, False), (True, True)):
            with self.subTest(enabled=enabled):
                self.configs.compact_on_exit = enabled
                self.processor._orchestrator.cancelled.is_set.return_value = cancelled
                self.processor.compact_on_exit()
        self.processor._orchestrator.compact_session.assert_not_called()

    def test_failure_is_reported_without_blocking_exit_or_retrying(self):
        self.processor._orchestrator.compact_session.side_effect = RuntimeError('offline')
        self.processor.compact_on_exit()
        self.processor.compact_on_exit()
        self.processor._orchestrator.compact_session.assert_called_once()
        self.events.reply.emit.assert_called_once()
        self.assertIn('preserved', self.events.reply.emit.call_args.kwargs['reply'].message)
