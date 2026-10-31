"""Listening time indicator; stopping capture is exclusively the recorder's job."""


def listening_timer(limit, stopped, render):
    elapsed = 0
    while not stopped.is_set():
        value = max(0, int(limit - elapsed)) if limit else elapsed
        render(f"{value // 60:02d}:{value % 60:02d}", elapsed > 0)
        if stopped.wait(1):
            break
        elapsed += 1
