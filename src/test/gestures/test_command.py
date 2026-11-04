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
        self.formatter.render_command.side_effect = lambda text: self.order.append(('print', text))
        self.events = Mock()
        self.speech, self.processor = Mock(), Mock()

        @contextmanager
        def loading(*_):
            self.order.append('loading')
            try:
                yield Mock()
            finally:
                self.order.append('closed')

        modules = {
            'askai.core.askai_configs': NS(configs=NS(is_sfx_muted=False)),
            'askai.core.permissions.grants': NS(grants=Mock()),
            'askai.core.processors.taius': NS(taius=Mock()),
            'askai.core.support.shared_instances': NS(
                shared=NS(speech=self.speech, mode=NS(processor=self.processor))),
            'askai.core.askai_settings': None,
            'askai.core.support.app_paths': NS(askai_data_dir=Mock(return_value='/tmp/gestures')),
            'askai.core.askai_messages': NS(msg=NS(t=lambda text: 'Translated: ' + text)),
            'askai.core.askai_events': NS(events=self.events),
            'askai.core.model.ai_reply': NS(AIReply=AIReply),
            'askai.cli.gestures_loading': NS(gestures_loading=loading),
        }
        output = patch.multiple('askai.cli.output', console=self.formatter.console,
                                render_command=self.formatter.render_command)
        output.start()
        self.addCleanup(output.stop)
        dependencies = patch.dict('sys.modules', modules)
        dependencies.start()
        self.addCleanup(dependencies.stop)

    def test_started_confirmation_uses_commander_after_preloader(self):
        result = {'status': 'started', 'pid': 123}
        with patch.object(command, 'authorize', return_value=True), patch.object(
                command, 'launch', return_value=result):
            self.assertEqual(command.start(1), result)
        message = 'Translated: Gesture control started.'
        self.formatter.render_command.assert_called_once_with(message)
        self.assertEqual(self.order, ['loading', 'closed', ('print', message)])
        self.events.reply.emit.assert_not_called()
        self.sound.assert_called_once_with('gesture-init.mp3')

    def test_failed_startup_does_not_print_success(self):
        with patch.object(command, 'authorize', return_value=True), patch.object(
                command, 'launch', side_effect=RuntimeError('Camera unavailable')):
            with self.assertRaisesRegex(RuntimeError, 'Camera unavailable'):
                command.start()
        self.assertEqual(self.order, ['loading', 'closed'])
        self.formatter.render_command.assert_not_called()
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
        self.speech.cancel_output.assert_called_once_with()
        self.processor.cancel.assert_called_once_with()
        self.events.abort.emit.assert_called_once_with(message='User interrupted [Heavy Metal]')
        self.assertEqual([call.args[0] for call in self.sound.call_args_list],
                         ['gesture-init.mp3', 'gesture-slide-up.mp3', 'gesture-slide-down.mp3',
                          'gesture-stop.mp3', 'gesture-quit.mp3', 'gesture-ptt.mp3'])

    def test_cancelled_authorization_does_not_start_or_print_success(self):
        with patch.object(command, 'authorize', return_value=False), patch.object(command, 'launch') as launch:
            self.assertEqual(command.start(), {'status': 'cancelled'})
        launch.assert_not_called()
        self.formatter.render_command.assert_not_called()
        self.sound.assert_not_called()
