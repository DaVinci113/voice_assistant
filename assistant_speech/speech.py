import pyttsx3

def get_greeting():
    pyttsx3.speak("    Я готова. Можете говорить. ")

def listen_command():
    pyttsx3.speak("    Да, Сэр. ")


if __name__ == '__main__':
    get_greeting()
    listen_command()