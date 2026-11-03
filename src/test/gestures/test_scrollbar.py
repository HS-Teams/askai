from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch
from askai.gestures import scrollbar


class ScrollbarTests(unittest.TestCase):
    def test_each_tick_moves_five_percent_of_total_range_in_either_direction(self):
        for minimum, maximum, current in ((0., 1., .5), (0., 2000., 900.), (10., 110., 60.)):
            for fraction in (.05, -.05):
                with self.subTest(bounds=(minimum, maximum), fraction=fraction):
                    access = Mock()
                    access.attribute.side_effect = [minimum, maximum, current]
                    access.number.side_effect = lambda value: value
                    self.assertTrue(scrollbar.move_scrollbar(access, 'bar', fraction))
                    access.set_number.assert_called_once_with('bar', 'AXValue', current - fraction * (maximum - minimum))

    def test_scroll_clamps_to_top_and_bottom_and_does_not_rewrite_endpoints(self):
        for current, fraction, target in ((.02, .05, 0.), (.98, -.05, 1.), (0., .05, 0.), (1., -.05, 1.)):
            with self.subTest(current=current, fraction=fraction):
                access = Mock()
                access.attribute.side_effect = [0., 1., current]
                access.number.side_effect = lambda value: value
                changed = scrollbar.move_scrollbar(access, 'bar', fraction)
                self.assertEqual(changed, current != target)
                if changed:
                    access.set_number.assert_called_once_with('bar', 'AXValue', target)
                else:
                    access.set_number.assert_not_called()

    def test_nested_content_uses_nearest_vertical_scrollbar_under_pointer(self):
        access = Mock()
        access.element_at.return_value = 'text'
        attributes = {('text', 'AXParent'): 'inner', ('inner', 'AXVerticalScrollBar'): 'inner_bar'}
        access.attribute.side_effect = lambda element, name: attributes.get((element, name))
        access.matches.return_value = False
        with patch.object(scrollbar, 'Accessibility') as factory, patch.object(scrollbar, 'move_scrollbar') as move:
            factory.return_value.__enter__.return_value = access
            scrollbar.scroll_fraction_at(NS(x=-400, y=200), -.05)
        move.assert_called_once_with(access, 'inner_bar', -.05)
        factory.return_value.__exit__.assert_called_once()

    def test_no_accessible_bar_reports_failure_without_synthetic_wheel_fallback(self):
        access = Mock()
        access.element_at.return_value = 'text'
        access.attribute.return_value = None
        access.matches.return_value = False
        with patch.object(scrollbar, 'Accessibility') as factory:
            factory.return_value.__enter__.return_value = access
            with self.assertRaisesRegex(scrollbar.ScrollBarUnavailable, 'No accessible vertical scrollbar'):
                scrollbar.scroll_fraction_at(NS(x=50, y=50), .05)
        access.set_number.assert_not_called()

    def test_pointer_can_target_the_vertical_scrollbar_itself(self):
        access = Mock()
        access.element_at.return_value = 'bar'
        access.attribute.return_value = None
        access.matches.side_effect = lambda element, name, value: value in ('AXScrollBar', 'AXVerticalOrientation')
        with patch.object(scrollbar, 'Accessibility') as factory, patch.object(scrollbar, 'move_scrollbar') as move:
            factory.return_value.__enter__.return_value = access
            scrollbar.scroll_fraction_at(NS(x=50, y=50), .05)
        move.assert_called_once_with(access, 'bar', .05)

    def test_invalid_range_does_not_change_position(self):
        for values in ((1., 0., .5), (0., float('inf'), .5), (0., 1., float('nan'))):
            access = Mock()
            access.attribute.side_effect = values
            access.number.side_effect = lambda value: value
            with self.assertRaises(scrollbar.ScrollBarUnavailable):
                scrollbar.move_scrollbar(access, 'bar', .05)
            access.set_number.assert_not_called()
