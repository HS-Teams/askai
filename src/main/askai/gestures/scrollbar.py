"""Move the accessible vertical scrollbar under the pointer by its actual range."""
from contextlib import ExitStack
import ctypes as ct
from math import isfinite


MAX_ANCESTORS = 64
CF_DOUBLE = 13
CF_UTF8 = 0x08000100
AX_ATTRIBUTE_UNSUPPORTED = -25205
AX_NO_VALUE = -25212


class ScrollBarUnavailable(RuntimeError):
    pass


def scroll_fraction_at(location, fraction):
    with Accessibility() as access:
        element = access.element_at(location)
        for _ in range(MAX_ANCESTORS):
            if not element:
                break
            bar = access.attribute(element, 'AXVerticalScrollBar')
            if not bar and access.matches(element, 'AXRole', 'AXScrollBar') and access.matches(
                    element, 'AXOrientation', 'AXVerticalOrientation'):
                bar = element
            if bar:
                return move_scrollbar(access, bar, fraction)
            element = access.attribute(element, 'AXParent')
    raise ScrollBarUnavailable('No accessible vertical scrollbar under the pointer')


def move_scrollbar(access, bar, fraction):
    minimum = access.number(access.attribute(bar, 'AXMinValue'))
    maximum = access.number(access.attribute(bar, 'AXMaxValue'))
    current = access.number(access.attribute(bar, 'AXValue'))
    if not all(isfinite(value) for value in (minimum, maximum, current, fraction)) or maximum < minimum:
        raise ScrollBarUnavailable('Invalid scrollbar range')
    target = max(minimum, min(maximum, current - fraction * (maximum - minimum)))
    if target == current:
        return False
    access.set_number(bar, 'AXValue', target)
    return True


class Accessibility(ExitStack):
    """Own the Core Foundation values returned by the macOS accessibility API."""
    def __init__(self):
        super().__init__()
        self.ax = ct.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        self.cf = ct.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        pointer = ct.c_void_p
        self._bind(self.ax, 'AXUIElementCreateSystemWide', pointer, [])
        self._bind(self.ax, 'AXUIElementCopyElementAtPosition', ct.c_int, [pointer, ct.c_float, ct.c_float, ct.POINTER(pointer)])
        self._bind(self.ax, 'AXUIElementCopyAttributeValue', ct.c_int, [pointer, pointer, ct.POINTER(pointer)])
        self._bind(self.ax, 'AXUIElementIsAttributeSettable', ct.c_int, [pointer, pointer, ct.POINTER(ct.c_bool)])
        self._bind(self.ax, 'AXUIElementSetAttributeValue', ct.c_int, [pointer, pointer, pointer])
        self._bind(self.ax, 'AXUIElementSetMessagingTimeout', ct.c_int, [pointer, ct.c_float])
        self._bind(self.cf, 'CFRelease', None, [pointer])
        self._bind(self.cf, 'CFStringCreateWithCString', pointer, [pointer, ct.c_char_p, ct.c_uint32])
        self._bind(self.cf, 'CFEqual', ct.c_bool, [pointer, pointer])
        self._bind(self.cf, 'CFGetTypeID', ct.c_ulong, [pointer])
        self._bind(self.cf, 'CFNumberGetTypeID', ct.c_ulong, [])
        self._bind(self.cf, 'CFNumberGetValue', ct.c_bool, [pointer, ct.c_int, pointer])
        self._bind(self.cf, 'CFNumberCreate', pointer, [pointer, ct.c_int, pointer])

    @staticmethod
    def _bind(library, name, result, arguments):
        function = getattr(library, name)
        function.restype, function.argtypes = result, arguments

    def _own(self, value):
        if value:
            self.callback(self.cf.CFRelease, value)
        return value

    def _string(self, value):
        return self._own(self.cf.CFStringCreateWithCString(None, value.encode('utf-8'), CF_UTF8))

    def element_at(self, location):
        system = self._own(self.ax.AXUIElementCreateSystemWide())
        self.ax.AXUIElementSetMessagingTimeout(system, .2)
        element = ct.c_void_p()
        error = self.ax.AXUIElementCopyElementAtPosition(system, location.x, location.y, ct.byref(element))
        value = self._own(element.value)
        if error or not value:
            raise ScrollBarUnavailable('Cannot access the element under the pointer')
        return value

    def attribute(self, element, name):
        value = ct.c_void_p()
        error = self.ax.AXUIElementCopyAttributeValue(element, self._string(name), ct.byref(value))
        result = self._own(value.value)
        if error in (AX_ATTRIBUTE_UNSUPPORTED, AX_NO_VALUE):
            return None
        if error:
            raise ScrollBarUnavailable(f'Cannot read {name} ({error})')
        return result

    def matches(self, element, attribute, expected):
        value = self.attribute(element, attribute)
        return bool(value and self.cf.CFEqual(value, self._string(expected)))

    def number(self, value):
        number = ct.c_double()
        if (not value or self.cf.CFGetTypeID(value) != self.cf.CFNumberGetTypeID()
                or not self.cf.CFNumberGetValue(value, CF_DOUBLE, ct.byref(number))):
            raise ScrollBarUnavailable('Scrollbar does not expose a numeric range')
        return number.value

    def set_number(self, element, attribute, value):
        name = self._string(attribute)
        settable = ct.c_bool()
        error = self.ax.AXUIElementIsAttributeSettable(element, name, ct.byref(settable))
        if error or not settable.value:
            raise ScrollBarUnavailable('This scrollbar does not support setting its position')
        number = ct.c_double(value)
        reference = self._own(self.cf.CFNumberCreate(None, CF_DOUBLE, ct.byref(number)))
        error = self.ax.AXUIElementSetAttributeValue(element, name, reference)
        if error:
            raise ScrollBarUnavailable(f'Cannot change scrollbar position ({error})')
