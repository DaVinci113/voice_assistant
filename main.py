import os
import time

from anyio import current_time

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import sounddevice as sd
import numpy as np
import queue
import sys

from ai import get_response

q = queue.Queue()
command_queue = queue.Queue()
audio_buffer = np.array([], dtype=np.float32)   # буфер для накопления речи

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy().flatten())

try:
    with sd.InputStream(samplerate=16000, channels=1, callback=callback):
        while True:
            try:
                chunk = q.get(timeout=0.1)
            except queue.Empty:
                continue


except KeyboardInterrupt:
    print("\n\n👋 Ассистент остановлен.")
except Exception as e:
    print(f"\nКритическая ошибка: {e}")