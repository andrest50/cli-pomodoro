from datetime import date

# Default settings
DEFAULT_POMODORO = 25
DEFAULT_SHORT_BREAK = 5
DEFAULT_LONG_BREAK = 10
DEFAULT_SESSIONS_UNTIL_LONG = 4
DEFAULT_AUTO_START = False
DEFAULT_USERNAME = "base_user"

# Session types
POMODORO = "pomodoro"
SHORT_BREAK = "short_break"
LONG_BREAK = "long_break"


class Settings:
    def __init__(self) -> None:
        self.pomodoro = DEFAULT_POMODORO
        self.short_break = DEFAULT_SHORT_BREAK
        self.long_break = DEFAULT_LONG_BREAK
        self.sessions_until_long = DEFAULT_SESSIONS_UNTIL_LONG
        self.auto_start = DEFAULT_AUTO_START

    def set_values(self, document):
        self.pomodoro = document["pomodoro"]
        self.short_break = document["short_break"]
        self.long_break = document["long_break"]
        self.sessions_until_long = document["sessions_until_long"]
        self.auto_start = document["auto_start"]

    def __str__(self) -> str:
        return f"Pomodoro: {self.pomodoro}\nShort break: {self.short_break}\nLong break: {self.long_break}\nSessions until long: {self.sessions_until_long}\nAuto start: {self.auto_start}"


class Day:
    def __init__(self) -> None:
        self.date = date.today().strftime("%m/%d/%y")
        self.time_studied = 0
        self.sessions_completed = 0

    def __str__(self) -> str:
        return f"Date: {self.date}\nTime studied: {self.time_studied}\nSessions completed: {self.sessions_completed}"

    def set_values(self, document):
        self.date = document["date"]
        self.time_studied = document["time_studied"]
        self.sessions_completed = document["sessions_completed"]


class User:
    def __init__(self) -> None:
        self.name = DEFAULT_USERNAME
        self.total_time_studied = 0
        self.days: list[Day] = []
        self.settings = Settings()

    def set_values(self, document):
        self.name = document["name"]
        self.total_time_studied = document["total_time_studied"]
        self.settings.set_values(document["settings"])
        for i, day in enumerate(document["days"]):
            self.days.append(Day())
            self.days[i].set_values(day)

    def get_session_length(self, session_type: str) -> int:
        if session_type == POMODORO:
            return self.settings.pomodoro
        elif session_type == SHORT_BREAK:
            return self.settings.short_break
        elif session_type == LONG_BREAK:
            return self.settings.long_break
        return 0

    def get_dict(self) -> dict[str, any]:
        user_dict = self.__dict__
        user_dict["settings"] = self.settings.__dict__
        for i, _ in enumerate(user_dict["days"]):
            user_dict["days"][i] = self.days[i].__dict__
        return user_dict

    def __str__(self) -> str:
        return f"Name: {self.name}\nTotal Time Studied: {self.total_time_studied}\nDays: {self.days}\nSettings: \n{self.settings}"


class Run:
    def __init__(self) -> None:
        self.current_session_type = POMODORO
        self.current_session_num = 1
        self.total_time_studied = 0
