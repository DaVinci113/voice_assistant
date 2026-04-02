import json
import time
import webbrowser

import sounddevice as sd
import queue
import sys

from vosk import Model, KaldiRecognizer
from assistant_speech.speech import Voice

import logging

from ai import get_response

from conf import SAMPLE_RATE, CHUNK_SIZE, MODEL_PATH, WAKE_WORDS, COMMAND_URL

logger = logging.getLogger(__name__)

model = Model(MODEL_PATH)

voice = Voice()


class AssistantState:
    def __init__(self):
        self.last_reset = 0
        self.time_out_reset = 1.8
        self.listening_state = False
        self.start_time_command = 0
        self.time_out_command = 10

def create_recognizer() -> KaldiRecognizer:
    """Создаём новый recognizer (сброс буфера)"""
    sample_rate = SAMPLE_RATE
    return KaldiRecognizer(model, sample_rate)

def check_wake_words(wake_word: tuple, recognize_text: str = None):
    if not recognize_text:
        return False
    return any(word in recognize_text for word in wake_word)

def shortener_url(url: str)->str:
    return url.split('.')[1]

def check_command_url(recognize_text: str, command_url: dict=COMMAND_URL)->str|None:
    if recognize_text:
        for command in command_url:
            for _ in command:
                if recognize_text in _ :
                    return command_url[command]

def opening_url(url: str):
    webbrowser.open(url)


def process_audio_chunk(chunk: bytes, recognizer: KaldiRecognizer, state: AssistantState, input_stream: sd.RawInputStream)-> KaldiRecognizer|None:

    if recognizer.AcceptWaveform(chunk):
        result = json.loads(recognizer.Result())
        text = result.get("text", "").strip()
        print("full text: ", text)
        if not text:
            return recognizer

        if state.listening_state:
            if url_name := check_command_url(recognize_text=text):
                try:
                    opening_url(url=url_name)
                    return recognizer
                except Exception as e:
                    recognizer.Reset()
            state.listening_state = False
            try:
                input_stream.stop()
                ai_response = get_response(text)
                voice.speak(ai_response)
            except Exception as e:
                print(e)
            finally:
                input_stream.start()
            recognizer.Reset()
        else:
            if check_wake_words(wake_word=WAKE_WORDS, recognize_text=text):
                state.listening_state = True
                voice.speak(voice.words["ready_to_listen"])
                state.start_time_command = time.time()
                recognizer.Reset()
    # else:
    #     partial = json.loads(recognizer.PartialResult())
    #     partial_text = partial.get("partial", "").strip()
    #     print("partial_text", partial_text)
    #     if not state.listening_state and partial_text:
    #         # threading.Thread(target=voice.speak(partial_text)).start()
    #         if check_wake_words(wake_word=WAKE_WORDS, recognize_text=partial_text):
    #             # threading.Thread(target=voice_ready_to_listen, daemon=True).start()
    #             # voice.speak(voice.words["ready_to_listen"])
    #             state.listening_state = True
    #             threading.Thread(target=voice.speak(partial_text)).start()
    #             # voice_ready_to_listen()
    #             # state.last_reset = current_time
    #             state.start_time_command = time.time()
    #
    #             # return create_recognizer()
    #             recognizer.Reset()
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
        if not q.full():
            q.put(bytes(indata))

    recognizer = create_recognizer()

    print("🎤 Ассистент запущен. Слушаю...")
    # voice_greeting()
    voice.speak(voice.words['greeting'])
    try:
        with (sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                dtype="int16",
                channels=1,
                blocksize=CHUNK_SIZE,
                callback=callback_bytes)) as stream:
            while True:

                try:
                    chunk = q.get_nowait()
                    recognizer = process_audio_chunk(chunk, recognizer, state, stream)
                    time.sleep(0.01)
                    print(state.listening_state)
                    # if state.listening_state:
                        # print(time.time() - state.start_time_command)

                    if state.listening_state and time.time() - state.start_time_command > state.time_out_command:
                        state.listening_state = False
                        recognizer.Reset()
                except queue.Empty:
                    continue

    except KeyboardInterrupt:
        print("\n\n👋 Ассистент остановлен.")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")

if __name__ == '__main__':
    main()
