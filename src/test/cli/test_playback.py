import unittest
from unittest.mock import Mock, patch
from askai.cli.playback import show_player, read_playback_key, Keyboard


class PlaybackTests(unittest.TestCase):
    def test_controls_replace_feedback_and_restore_same_line(self):
        player, console = Mock(), Mock()
        player.status.return_value = {'path': '/music/song.mp3', 'state': 'playing'}
        player.volume.return_value = 50
        read = Mock(side_effect=['+', '-', 'a', 'p', 'q'])
        with patch('askai.cli.playback.Live') as live, patch('askai.cli.playback.sleep'):
            show_player(player, console, read, lambda text: text)
        self.assertEqual([c.args[0] for c in player.control.call_args_list], ['pause', 'play'])
        console.print.assert_called_once()
        updates = live.return_value.__enter__.return_value.update.call_args_list
        self.assertEqual([updates[i].args[0].plain for i in (0, 2, 4, 6)],
                         ['Volume up', 'Volume down', 'Pause playback', 'Resume playback'])
        for i in (1, 3, 5, 7):
            self.assertIn('[p] Resume playback', updates[i].args[0].plain)
        self.assertTrue(all(not call.args for call in read.call_args_list))

    def test_stop_and_no_playback(self):
        player, console = Mock(), Mock()
        player.status.side_effect = [{'path': '/movie.mp4', 'state': 'playing'}, None]
        player.volume.return_value = 50
        with patch('askai.cli.playback.Live') as live, patch('askai.cli.playback.sleep'):
            show_player(player, console, Mock(return_value='s'), lambda text: text)
        player.control.assert_called_once_with('stop')
        self.assertEqual(live.return_value.__enter__.return_value.update.call_args.args[0].plain,
                         'No active AskAI media playback')

    def test_keyboard_module_reads_one_key_without_line_input(self):
        with patch.object(Keyboard, 'wait_keystroke', return_value=Keyboard.VK_ESC) as read:
            self.assertEqual(read_playback_key(), '\x1b')
            read.assert_called_once_with(ignore_error_keys=True)

    def test_escape_closes_without_stopping_media(self):
        player = Mock()
        player.status.return_value = {'path': '/song.mp3', 'state': 'playing'}
        with patch('askai.cli.playback.Live'):
            show_player(player, Mock(), Mock(return_value='\x1b'), lambda text: text)
        player.control.assert_not_called()

    def test_media_ending_while_waiting_for_key_is_a_status_not_an_error(self):
        from askai.core.capabilities.media_player import PlaybackEnded
        player = Mock()
        player.status.return_value = {'path': '/song.mp3', 'state': 'playing'}
        player.volume.return_value = 25
        player.control.side_effect = PlaybackEnded('No active AskAI media playback')
        with patch('askai.cli.playback.Live') as live:
            show_player(player, Mock(), Mock(return_value='a'), lambda text: text)
        self.assertEqual(live.return_value.__enter__.return_value.update.call_args.args[0].plain,
                         'Playback has ended')
