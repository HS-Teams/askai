from contextlib import contextmanager
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch
from askai.gestures import command
from askai.core.model.ai_reply import AIReply


class GestureCommandTests(unittest.TestCase):
    def setUp(self):
        sound = patch('askai.gestures.sfx._play')
        self.sound = sound.start()
        self.addCleanup(sound.stop)
        self.order = []
        self.formatter = Mock()
        self.formatter.commander_print.side_effect = lambda text: self.order.append(('print', text))
        self.events = Mock()

        @contextmanager
        def loading(*_):
            self.order.append('loading')
            try:
                yield Mock()
            finally:
                self.order.append('closed')

        modules = {
            'askai.core.permissions.grants': NS(grants=Mock()),
            'askai.core.processors.taius': NS(taius=Mock()),
            'askai.core.support.app_paths': NS(askai_data_dir=Mock(return_value='/tmp/gestures')),
            'askai.core.askai_messages': NS(msg=NS(t=lambda text: 'Translated: ' + text)),
            'askai.core.askai_events': NS(events=self.events),
            'askai.core.model.ai_reply': NS(AIReply=AIReply),
            'askai.core.support.text_formatter': NS(text_formatter=self.formatter),
            'askai.cli.gestures_loading': NS(gestures_loading=loading),
        }
        dependencies = patch.dict('sys.modules', modules)
        dependencies.start()
        self.addCleanup(dependencies.stop)

    def test_started_confirmation_uses_commander_after_preloader(self):
        result = {'status': 'started', 'pid': 123}
        with patch.object(command, 'authorize', return_value=True), patch.object(
                command, 'launch', return_value=result):
            self.assertEqual(command.start(1), result)
        message = 'Translated: Gesture control started.'
        self.formatter.commander_print.assert_called_once_with(message)
        self.assertEqual(self.order, ['loading', 'closed', ('print', message)])
        self.events.reply.emit.assert_not_called()
        self.sound.assert_called_once_with('gesture-init.mp3')

    def test_failed_startup_does_not_print_success(self):
        with patch.object(command, 'authorize', return_value=True), patch.object(
                command, 'launch', side_effect=RuntimeError('Camera unavailable')):
            with self.assertRaisesRegex(RuntimeError, 'Camera unavailable'):
                command.start()
        self.assertEqual(self.order, ['loading', 'closed'])
        self.formatter.commander_print.assert_not_called()
        self.sound.assert_not_called()

    def test_worker_notices_are_system_messages_and_voice_keeps_its_action(self):
        with patch.object(command, 'authorize', return_value=True), patch.object(
                command, 'launch', return_value={'status': 'started'}) as launch:
            command.start()
        notify = launch.call_args.args[3]
        for kind, message in command.MESSAGES.items():
            with self.subTest(kind=kind):
                self.events.reply.emit.reset_mock()
                notify(kind)
                self.events.reply.emit.assert_called_once_with(reply=AIReply.system(message))
                reply = self.events.reply.emit.call_args.kwargs['reply']
                self.assertTrue(reply.is_system)
                self.assertFalse(reply.is_speakable)
        self.events.reply.emit.reset_mock()
        notify('voice')
        self.events.voice_input.emit.assert_called_once_with()
        self.events.reply.emit.assert_not_called()
        self.assertEqual([call.args[0] for call in self.sound.call_args_list],
                         ['gesture-init.mp3', 'gesture-quit.mp3', 'gesture-ptt.mp3'])

    def test_cancelled_authorization_does_not_start_or_print_success(self):
        with patch.object(command, 'authorize', return_value=False), patch.object(command, 'launch') as launch:
            self.assertEqual(command.start(), {'status': 'cancelled'})
        launch.assert_not_called()
        self.formatter.commander_print.assert_not_called()
        self.sound.assert_not_called()
