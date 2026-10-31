"""Play PCM chunks as they arrive without waiting for the complete synthesis."""
from contextlib import suppress
import subprocess


class StartedSpeechError(RuntimeError):
    """Speech may already be audible; never replay it through another provider."""


def play_pcm_chunks(chunks, sample_rate, tempo, cancelled):
    process = None
    audio = bytearray()
    try:
        for chunk in chunks:
            if cancelled.is_set():
                return None
            if not chunk:
                continue
            if process is None:
                process = subprocess.Popen(
                    ['ffplay', '-v', 'error', '-nodisp', '-autoexit', '-probesize', '32',
                     '-analyzeduration', '0', '-f', 's16le', '-ar', str(sample_rate),
                     '-ch_layout', 'mono', '-af', f'atempo={tempo}', '-i', 'pipe:0'],
                    stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            audio.extend(chunk)
            process.stdin.write(chunk)
            process.stdin.flush()
        if process is None or len(audio) % 2:
            raise ValueError('Incomplete PCM speech stream')
        process.stdin.close()
        while process.poll() is None:
            if cancelled.wait(.05):
                return None
        if process.returncode:
            raise RuntimeError('Streaming speech playback failed')
        return bytes(audio)
    except Exception as error:
        if process is not None:
            raise StartedSpeechError('Speech stream interrupted; partial speech was not replayed') from error
        raise
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.wait()
            if not process.stdin.closed:
                # Cleanup must not replace the playback error with BrokenPipeError.
                with suppress(OSError):
                    process.stdin.close()
