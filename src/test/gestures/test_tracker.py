import unittest
from types import SimpleNamespace
from askai.gestures.tracker import right_hand_points


def result_for(*labels):
    return SimpleNamespace(
        hand_landmarks=[[SimpleNamespace(x=i / 10, y=.3)] * 21 for i in range(len(labels))],
        handedness=[[SimpleNamespace(category_name=label, score=.95)] for label in labels],
    )


class RightHandTests(unittest.TestCase):
    def test_right_hand_selected_regardless_of_detection_order(self):
        for labels in [('Left', 'Right'), ('Right', 'Left')]:
            result = result_for(*labels)
            self.assertEqual(right_hand_points(result), [(labels.index('Right') / 10, .3)] * 21)

    def test_left_hand_never_takes_control(self):
        self.assertEqual(right_hand_points(result_for('Left')), [])
        self.assertEqual(right_hand_points(result_for()), [])

    def test_missing_classification_does_not_control_pointer(self):
        result = result_for('Right')
        result.handedness = [[]]
        self.assertEqual(right_hand_points(result), [])
