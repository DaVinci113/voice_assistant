import pyttsx3

def voice_greeting():
    pyttsx3.speak("    Я готова. Можете говорить. ")

def voice_listen_command():
    pyttsx3.speak("    Да, Сэр. ")

def voice_answer(text):
    pyttsx3.speak(text)


if __name__ == '__main__':
    # voice_greeting()
    # voice_listen_command()
    voice_answer("Я пришёл к тебе с приветом рассказать, что солнце встало!")