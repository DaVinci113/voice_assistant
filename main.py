import json
import os
import time

import sounddevice as sd
import numpy as np
import queue
import sys
from vosk import Model, KaldiRecognizer

from conf import SAMPLE_RATE, CHUNK_SIZE, MODEL_PATH, WAKE_WORD

from ai import get_response
def recognize_audio(chunk: sd.RawInputStream, recognizer: KaldiRecognizer):

    if recognizer.AcceptWaveform(chunk):
        result = json.loads(recognizer.Result())
        text = result.get("text", "").strip()
        print(text)
    else:
        partial = json.loads(recognizer.PartialResult())
        partial_text = partial.get("partial", "").strip()
        if partial_text:
            print(f"Partial: {partial_text}")

def main():
    q = queue.Queue()

    try:
        model = Model(MODEL_PATH)
        print("Model loaded.")
    except Exception as e:
        print("Model not found.")
        raise e

    def callback_bytes(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))

    recognizer = KaldiRecognizer(model, SAMPLE_RATE)

    print("🎤 Ассистент запущен. Слушаю 'Alexa'...")
    try:
        with sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                dtype="int16",
                channels=1,
                blocksize=CHUNK_SIZE,
                callback=callback_bytes):
            while True:

                try:
                    chunk = q.get(timeout=1)
                    recognize_audio(chunk, recognizer)

                except queue.Empty:
                    continue

    except KeyboardInterrupt:
        print("\n\n👋 Ассистент остановлен.")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")

if __name__ == '__main__':
    main()
