import unittest
from unittest.mock import Mock, call, patch

from askai.core.support import clipboard


class ClipboardTests(unittest.TestCase):
    def test_paste_targets_focused_app_and_never_presses_enter(self):
        appkit, quartz, services = Mock(), Mock(), Mock()
        appkit.NSWorkspace.sharedWorkspace.return_value.frontmostApplication.return_value.processIdentifier.return_value = 42
        down, up = object(), object()
        quartz.CGEventCreateKeyboardEvent.side_effect = [down, up]
        with patch.object(clipboard.sys, 'platform', 'darwin'), patch.object(
                clipboard.ctypes, 'CDLL', return_value=services), patch.dict(
                'sys.modules', {'AppKit': appkit, 'Quartz': quartz}):
            clipboard.paste_into_focused_app()
        self.assertEqual(quartz.CGEventCreateKeyboardEvent.call_args_list,
                         [call(None, 9, True), call(None, 9, False)])
        self.assertEqual(quartz.CGEventSetFlags.call_args_list,
                         [call(down, quartz.kCGEventFlagMaskCommand), call(up, quartz.kCGEventFlagMaskCommand)])
        self.assertEqual(quartz.CGEventPostToPid.call_args_list, [call(42, down), call(42, up)])

    def test_permission_failure_or_missing_focus_sends_no_keys(self):
        for trusted in (False, True):
            with self.subTest(trusted=trusted):
                appkit, quartz, services = Mock(), Mock(), Mock()
                services.AXIsProcessTrusted.return_value = trusted
                appkit.NSWorkspace.sharedWorkspace.return_value.frontmostApplication.return_value = None
                with patch.object(clipboard.sys, 'platform', 'darwin'), patch.object(
                        clipboard.ctypes, 'CDLL', return_value=services), patch.dict(
                        'sys.modules', {'AppKit': appkit, 'Quartz': quartz}):
                    with self.assertRaisesRegex(RuntimeError, 'No focused application' if trusted else 'Accessibility'):
                        clipboard.paste_into_focused_app()
                quartz.CGEventPostToPid.assert_not_called()

    def test_other_platforms_report_unsupported_paste(self):
        with patch.object(clipboard.sys, 'platform', 'linux'), patch.object(clipboard.ctypes, 'CDLL') as library:
            with self.assertRaisesRegex(RuntimeError, 'requires macOS'):
                clipboard.paste_into_focused_app()
        library.assert_not_called()
