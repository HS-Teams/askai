import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from askai.core.speech import dictation


class DictationTests(unittest.TestCase):
    def test_refinement_is_structured_and_preserves_source(self):
        complete = Mock(return_value=json.dumps({'final_text': 'Olá, NASA!'}))
        original = 'Olá NASA'
        self.assertEqual(dictation.refine(original, 'instructions', complete), 'Olá, NASA!')
        self.assertEqual(complete.call_args.args[0][1]['content'], original)
        self.assertEqual(complete.call_args.kwargs['schema'], dictation.REFINEMENT_SCHEMA)

    def test_invalid_refinement_is_rejected(self):
        for response in ('reasoning', '[]', '{}', '{"final_text": " "}',
                         '{"final_text": 1}', '{"final_text":"ok","reason":"why"}'):
            with self.subTest(response=response), self.assertRaises(ValueError):
                dictation.refine('source', 'instructions', Mock(return_value=response))

    def test_source_survives_refinement_failure_and_files_never_overwrite(self):
        with TemporaryDirectory() as directory:
            destination = Path(directory) / 'text.txt'
            dictation.validate_destination(destination)
            source = dictation.save_original(destination, 'API original')
            with self.assertRaises(RuntimeError):
                dictation.refine('API original', 'instructions', Mock(side_effect=RuntimeError))
            self.assertEqual(source.read_text(), 'API original')
            self.assertFalse(destination.exists())
            with self.assertRaises(FileExistsError):
                dictation.validate_destination(destination)
            dictation.save_refined(destination, 'API refined')
            with self.assertRaises(FileExistsError):
                dictation.save_refined(destination, 'overwrite')
            with self.assertRaises(FileExistsError):
                dictation.save_original(destination, 'overwrite')
            self.assertEqual(destination.read_text(), 'API refined')

    def test_relative_destination_and_missing_parent(self):
        dictation.validate_destination(Path('unused-dictation-test.txt'))
        with TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                dictation.validate_destination(Path(directory) / 'missing' / 'text.txt')
