SAMPLE_RATE = 16000
CHUNK_SIZE = 8000
MODEL_PATH = "vosk-model-small-ru-0.22"
WAKE_WORDS = ("пелагея", "жорик",)

COMMAND_URL = {
    ('открой ютуб,', 'открой ютюб,'): 'https://www.youtube.com/',
    ('открой гугл,', 'открой гугол,'): 'https://www.google.com/',
    ('открой роблокс,', 'открой роблакс,'): 'https://www.roblox.com/',
}