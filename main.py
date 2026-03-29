import json
import os
import time

import sounddevice as sd
import numpy as np
import queue
import sys
from vosk import Model, KaldiRecognizer
from assistant_speech.speech import get_greeting, listen_command
import logging

from ai import get_response

from conf import SAMPLE_RATE, CHUNK_SIZE, MODEL_PATH, WAKE_WORDS

logger = logging.getLogger(__name__)


class AssistantState:
    def __init__(self):
        self.listening_state = False
        self.start_time_command = 0
        self.time_out_command = 8

def recognize_audio(chunk: sd.RawInputStream, recognizer: KaldiRecognizer, state: AssistantState)-> str|None:
    logger.info("recognize_audio")
    print("recognize_audio")

    if recognizer.AcceptWaveform(chunk):
        result = json.loads(recognizer.Result())
        text = result.get("text", "").strip()
        if text:
            print(text)
            return text
    else:
        partial = json.loads(recognizer.PartialResult())
        partial_text = partial.get("partial", "").strip()
        if partial_text:
            print(f"Partial: {partial_text}")

def check_wake_words(wake_word: tuple, recognize_text: str = None):
    return any(word in recognize_text for word in wake_word)

def main():
    logging.basicConfig(filename='myapp.log', level=logging.INFO)
    logger.info('Started')
    q = queue.Queue()
    state = AssistantState()

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
    get_greeting()
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
                    result = recognize_audio(chunk, recognizer, state)
                    if result:
                        if check_wake_words(wake_word=WAKE_WORDS, recognize_text=result):
                            listen_command()
                            state.listening_state = True
                    print(state.listening_state)


                except queue.Empty:
                    continue

    except KeyboardInterrupt:
        print("\n\n👋 Ассистент остановлен.")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")

if __name__ == '__main__':
    main()
