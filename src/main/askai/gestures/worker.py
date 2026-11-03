"""Camera/UI main thread in a dedicated process, independent of the AskAI prompt."""
from contextlib import ExitStack
import json
import os
import signal
import sys
from threading import Event, Thread


def read_controls(stream, paused):
    for line in stream:
        if line.strip() == 'pause':
            paused.set()
        elif line.strip() == 'resume':
            paused.clear()
        elif line.strip() in ('mute_sfx', 'unmute_sfx'):
            from askai.core.speech.effects import set_muted
            set_muted(line.strip() == 'mute_sfx')


def main():
    parent_pid = os.getppid()
    camera_index, event_fd = map(int, sys.argv[1:3])
    labels = json.loads(sys.argv[3])
    from askai.core.speech.effects import set_muted
    set_muted(sys.argv[4] == '1')
    with os.fdopen(event_fd, 'w', buffering=1) as output:
        def notify(kind):
            output.write(json.dumps(kind) + '\n')

        def interrupted(*_):
            raise KeyboardInterrupt

        signal.signal(signal.SIGTERM, interrupted)
        paused = Event()
        Thread(target=read_controls, args=(sys.stdin, paused), daemon=True).start()
        notify({'type': 'loading', 'stage': 'imports'})
        from askai.gestures.preview import Pointer, Preview
        from askai.gestures.tracker import HandTracker, model_path, pose_model_path
        from askai.gestures.session import run_session
        from askai.core.permissions.grants import grants
        from askai.core.support.app_paths import askai_data_dir
        import cv2
        with ExitStack() as resources:
            notify({'type': 'loading', 'stage': 'pointer'})
            pointer = Pointer()
            resources.callback(pointer.release)
            notify({'type': 'loading', 'stage': 'model'})
            path = model_path(askai_data_dir())
            notify({'type': 'loading', 'stage': 'body_model'})
            pose_path = pose_model_path(askai_data_dir())
            notify({'type': 'loading', 'stage': 'detector'})
            tracker = HandTracker(path, pose_path)
            resources.callback(tracker.close)
            notify({'type': 'loading', 'stage': 'camera'})
            camera = cv2.VideoCapture(camera_index)
            resources.callback(camera.release)
            if not camera.isOpened():
                raise RuntimeError('Cannot open the gesture camera')
            notify({'type': 'loading', 'stage': 'preview'})
            view = Preview(lambda text: labels[text])
            resources.callback(view.close)
            notify('started')
            resources.pop_all()
            run_session(camera, tracker, pointer, view, grants, notify=notify,
                        should_stop=lambda: os.getppid() != parent_pid, should_pause=paused.is_set)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
