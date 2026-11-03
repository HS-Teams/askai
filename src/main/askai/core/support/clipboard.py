"""Paste through the focused application's native clipboard action."""
import ctypes
import sys


PASTE_KEY_CODE = 9  # macOS virtual key for V.


def paste_into_focused_app():
    if sys.platform != 'darwin':
        raise RuntimeError('Pasting into another application currently requires macOS')
    services = ctypes.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
    services.AXIsProcessTrusted.restype = ctypes.c_bool
    if not services.AXIsProcessTrusted():
        raise RuntimeError('Enable Accessibility permission for your terminal in macOS System Settings, then retry /paste')

    import AppKit
    import Quartz

    application = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
    if application is None:
        raise RuntimeError('No focused application to receive the clipboard contents')
    pid = application.processIdentifier()
    for pressed in (True, False):
        event = Quartz.CGEventCreateKeyboardEvent(None, PASTE_KEY_CODE, pressed)
        Quartz.CGEventSetFlags(event, Quartz.kCGEventFlagMaskCommand)
        Quartz.CGEventPostToPid(pid, event)
