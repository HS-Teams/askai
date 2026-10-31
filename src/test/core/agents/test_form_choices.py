import unittest
from askai.core.agents.elicitation import decode_form, field_label


class FormChoiceTests(unittest.TestCase):
    field = {'type': 'string', 'title': 'Action', 'oneOf': [
        {'const': 'skip', 'title': 'Skip'}, {'const': 'merge', 'title': 'Merge'},
    ]}

    def test_numbered_choice_maps_to_protocol_value(self):
        schema = {'type': 'object', 'properties': {'action': self.field}}
        self.assertEqual(decode_form(schema, {'action': '2'}), {'action': 'merge'})
        self.assertEqual(decode_form(schema, {'action': 'merge'}), {'action': 'merge'})
        self.assertEqual(decode_form(schema, {'action': ''}), {})

    def test_titles_translated_without_changing_identifiers(self):
        translate = lambda value: {'Action': 'Ação', 'Skip': 'Ignorar', 'Merge': 'Mesclar'}.get(value, value)
        rendered = field_label('action', self.field, translate)
        self.assertIn('(1) Ignorar', rendered)
        self.assertIn('(2) Mesclar', rendered)
        self.assertNotIn('const', rendered)
        self.assertEqual(self.field['oneOf'][1]['const'], 'merge')
