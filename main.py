import json
import time

import sounddevice as sd
import queue
import sys

from vosk import Model, KaldiRecognizer
from assistant_speech.speech import voice_answer, voice_greeting, voice_listen_command
import logging

from ai import get_response

from conf import SAMPLE_RATE, CHUNK_SIZE, MODEL_PATH, WAKE_WORDS

logger = logging.getLogger(__name__)

model = Model(MODEL_PATH)

class AssistantState:
    def __init__(self):
        self.listening_state = False
        self.start_time_command = 0
        self.time_out_command = 8

def create_recognizer() -> KaldiRecognizer:
    """Создаём новый recognizer (сброс буфера)"""
    sample_rate = SAMPLE_RATE
    return KaldiRecognizer(model, sample_rate)

def check_wake_words(wake_word: tuple, recognize_text: str = None):
    if not recognize_text:
        return False
    return any(word in recognize_text for word in wake_word)


def process_audio_chunk(chunk: bytes, recognizer: KaldiRecognizer, state: AssistantState, input_stream: sd.RawInputStream)-> KaldiRecognizer|None:

    if recognizer.AcceptWaveform(chunk):
        result = json.loads(recognizer.Result())
        text = result.get("text", "").strip()
        if not text:
            return recognizer

        if state.listening_state:
            state.listening_state = False
            try:
                input_stream.stop()
                ai_response = get_response(text)
                voice_answer(text=ai_response)
            except Exception as e:
                print(e)
            finally:
                input_stream.start()
            return create_recognizer()

        else:
            if check_wake_words(wake_word=WAKE_WORDS, recognize_text=text):
                state.listening_state = True
                state.start_time_command = time.time()
                return create_recognizer()

    else:
        partial = json.loads(recognizer.PartialResult())
        partial_text = partial.get("partial", "").strip()
        if not state.listening_state and partial_text:
            if check_wake_words(wake_word=WAKE_WORDS, recognize_text=partial_text):
                voice_listen_command()
                state.listening_state = True
                state.start_time_command = time.time()
                return create_recognizer()
    return recognizer



def main():
    logging.basicConfig(filename='myapp.log', level=logging.INFO)
    logger.info('Started')
    q = queue.Queue()
    state = AssistantState()

    try:
        print("Model loaded.")
    except Exception as e:
        print("Model not found.")
        raise e

    def callback_bytes(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))

    recognizer = create_recognizer()

    print("🎤 Ассистент запущен. Слушаю...")
    voice_greeting()
    try:
        with (sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                dtype="int16",
                channels=1,
                blocksize=CHUNK_SIZE,
                callback=callback_bytes)) as stream:
            while True:

                try:
                    chunk = q.get(timeout=1)
                    recognizer = process_audio_chunk(chunk, recognizer, state, stream)
                    print(state.listening_state)

                    if state.listening_state and time.time() - state.start_time_command > state.time_out_command:
                        state.listening_state = False
                        recognizer = create_recognizer()

                except queue.Empty:
                    continue

    except KeyboardInterrupt:
        print("\n\n👋 Ассистент остановлен.")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")

if __name__ == '__main__':
    main()
