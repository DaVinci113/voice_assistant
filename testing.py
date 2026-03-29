import queue
import sys
import time

import numpy as np
import sounddevice as sd


SAMPLE_RATE = 16000
duration = 5

q = queue.Queue()
audio_buffer = np.array([], dtype=np.float32)
chunks = []

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy().flatten())

try:
    with sd.InputStream(samplerate=SAMPLE_RATE, dtype="float32", channels=1, callback=callback):
        start = time.time()
        print("start")
        while time.time() - start < duration:
            try:
                chunk = q.get(timeout=0.1)
                chunks.append(chunk)
            except queue.Empty:
                continue
except KeyboardInterrupt:
    print("Shutting down")
except Exception as e:
    print(e)

while not q.empty():
    try:
        chunks.append(q.get_nowait())
    except queue.Empty:
        break
if chunks:
    audio_buffer = np.concatenate(chunks)
else:
    audio_buffer = np.array([], dtype=np.float32)
sd.play(audio_buffer, SAMPLE_RATE)
sd.wait()

