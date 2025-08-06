# memory.py
class UserSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.history = []  # 최근 N개만 쌓기
        self.profile = {}
        self.consent_given = False  # 개인정보 동의 여부

    def add_message(self, speaker, text):
        self.history.append({"role": speaker, "content": text})
        if len(self.history) > 10:
            self.history = self.history[-10:]

    def set_profile(self, key, value):
        self.profile[key] = value

    def give_consent(self):
        self.consent_given = True
