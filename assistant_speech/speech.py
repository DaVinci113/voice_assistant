import pyttsx3


class Voice:
    def __init__(self):
        self.engine = pyttsx3.init()

        self.words = {
            "greeting": "Я готова к работе. Можете говорить!",
            "ready_to_listen": "Да, Сэр!",
            "opening_url": "Открываю ",
            "ai_answer": "",
        }

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

if __name__ == '__main__':
    voice = Voice()
    voice.speak(voice.words["greeting"])
    print(1+1)
    voice.speak(voice.words["ready_to_listen"])
    voice.speak(voice.words["opening_url"]+"youtube")
    # voice.listen_command()
    # voice.url_opening("youtube")
    # voice_listen_command()
    # voice_answer("Я пришёл к тебе с приветом рассказать, что солнце встало!")