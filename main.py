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
# file_logging = logging.FileHandler('voice_assistant.log')
# file_logging.setLevel(logging.WARNING)
# console_logging = logging.StreamHandler()
# console_logging.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s"
)

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
    logging.info("")
    return KaldiRecognizer(model, sample_rate)

def check_wake_words(wake_word: tuple, recognize_text: str = None):
    """Распознавание wake-word"""
    if not recognize_text:
        return False
    logging.info("Распознано wake_word")
    return any(word in recognize_text for word in wake_word)

def shortener_url(url: str)->str:
    """Выявление ссылки для открытия"""
    url_address = url.split('.')[1]
    logging.info(f"Ссылка для открытия {url_address}")
    return url_address

def check_command_url(recognize_text: str, command_url: dict=COMMAND_URL)->str|None:
    """Распознавание команды для открытия"""
    if recognize_text:
        for command in command_url:
            for _ in command:
                if recognize_text in _ :
                    result = command_url[command]
                    logging.info(f"Команда для открытия{result}")
                    return result

def opening_url(url: str):
    """Открытие ссылки в браузере"""
    logging.info(f"Открываю в браузере {url}")
    webbrowser.open(url)


def process_audio_chunk(chunk: bytes, recognizer: KaldiRecognizer, state: AssistantState, input_stream: sd.RawInputStream)-> KaldiRecognizer|None:
    """Обработка чанков с микрофона"""

    if recognizer.AcceptWaveform(chunk):
        result = json.loads(recognizer.Result())
        text = result.get("text", "").strip()
        logging.info(f"Распонанный текст: {text}")
        if not text:
            return recognizer

        if state.listening_state:
            if url := check_command_url(recognize_text=text):
                try:
                    url_name = shortener_url(url=url)
                    voice.speak(voice.words["opening_url"]+url_name)
                    opening_url(url=url)
                    return recognizer
                except Exception as e:
                    recognizer.Reset()
            state.listening_state = False
            try:
                input_stream.stop()
                ai_response = get_response(text)
                logger.debug(f"Ответ ИИ: {ai_response}")
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
    else:
        partial = json.loads(recognizer.PartialResult())
        partial_text = partial.get("partial", "").strip()
        logger.debug(f"Частично распознанный текст: {partial_text}")
        if not state.listening_state and partial_text:
            if check_wake_words(wake_word=WAKE_WORDS, recognize_text=partial_text):
                voice.speak(voice.words["ready_to_listen"])
                state.listening_state = True
                state.start_time_command = time.time()

                recognizer.Reset()

    return recognizer



def main():
    logging.info("Приложение запущено")
    q = queue.Queue()
    state = AssistantState()

    try:
        logging.debug("Модель загружена")
    except Exception as e:
        logging.error("Ошибка загрузка модели")
        raise e

    def callback_bytes(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        if not q.full():
            q.put(bytes(indata))

    recognizer = create_recognizer()

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
                    logging.debug("Статус прослушивания команды")

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
