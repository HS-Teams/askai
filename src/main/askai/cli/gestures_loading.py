"""A single spinner line follows actual gesture worker startup stages."""
from contextlib import contextmanager
from rich.text import Text

STAGES = {
    'imports': 'Loading gesture libraries...',
    'pointer': 'Preparing mouse control...',
    'model': 'Preparing gesture model...',
    'body_model': 'Preparing body detection model...',
    'detector': 'Starting hand and body detectors...',
    'camera': 'Opening gesture camera...',
    'preview': 'Preparing gesture preview...',
}


@contextmanager
def gestures_loading(console, translate):
    labels = {stage: Text(translate(message)) for stage, message in STAGES.items()}
    with console.status(labels['imports'], spinner='dots') as status:
        yield lambda stage: status.update(labels[stage])
