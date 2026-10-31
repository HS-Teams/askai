import unittest
from unittest.mock import Mock
from askai.core.component.answer_validator import validate_response
from askai.exception.exceptions import InaccurateResponse


class ValidatorTests(unittest.TestCase):
    def test_assessment_is_validated_without_repair(self):
        model = Mock()
        model.complete.return_value = (
            '{"color":"Green","accuracy":90,"reasoning":"Evidence verified","tips":""}'
        )
        result = validate_response(model, "{response}", response="result")
        self.assertEqual(result.color, "Green")
        self.assertEqual(result.accuracy, 90)

    def test_invalid_payloads_are_rejected(self):
        model = Mock()
        for payload in [
            "prose",
            "{}",
            '{"color":"Unknown","accuracy":101,"reasoning":"","tips":""}',
        ]:
            with self.subTest(payload=payload), self.assertRaises(InaccurateResponse):
                model.complete.return_value = payload
                validate_response(model, "{response}", response="result")
