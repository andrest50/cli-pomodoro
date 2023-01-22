from rich.console import Console
from rich.table import Table
from datetime import timedelta, date
from tinydb import TinyDB, Query
import time
import sys
import cursor

# Session types
POMODORO = "pomodoro"
SHORT_BREAK = "short_break"
LONG_BREAK = "long_break"
INVALID = "invalid"

# Default settings
DEFAULT_POMODORO = 25
DEFAULT_SHORT_BREAK = 5
DEFAULT_LONG_BREAK = 10
DEFAULT_SESSIONS_UNTIL_LONG = 4
DEFAULT_AUTO_START = False
DEFAULT_USERNAME = "base_user"

# Reused string literals for faster autocompletion and readability
SETTINGS = "settings"
CURRENT_SESSION_TYPE = "current_session_type"
CURRENT_SESSION_NUM = "current_session_num"
AUTO_START = "auto_start"
SESSIONS_COMPLETED = "sessions_completed"
TIME_STUDIED = "time_studied"
TOTAL_TIME_STUDIED = "total_time_studied"
SESSIONS_UNTIL_LONG = "sessions_until_long"
DAYS = "days"
DATE = "date"


def show_time_left(console, time_left):
    """
    Function called every second timer is active
    """
    console.print(f"{time_left}", end="\r")


def start_timer(console, session_length_sec):
    """
    Function for running the timer
    """
    time_left_seconds = session_length_sec

    # Run the timer until the timer hits zero or user signal to stop
    active = True
    while active:
        try:
            # Update the timer and print the time to the terminal
            while time_left_seconds >= 0:
                # Convert seconds into timedelta object
                time_left = timedelta(seconds=time_left_seconds)
                show_time_left(console, time_left)  # Print time left
                time.sleep(1.0)  # Wait a second to update time
                time_left_seconds -= 1
            active = False
            print("")

        # If the user is trying to exit the timer or program by sending a signal (Ctrl-C)
        except KeyboardInterrupt:
            console.print("\nTime paused!", style="bold red")
            console.print("(1) Continue", style="bold red")
            console.print("(2) Finish early", style="bold red")
            again = True

            # Prompt the user for input until it is validly provided
            while again:
                option = get_user_input(console)

                # User input of 1 to continue timer and 2 to end timer
                if option == 1:
                    again = False
                elif option == 2:
                    return session_length_sec - time_left_seconds

    # Notification that the timer is up
    console.print("Time is up!", style="bold red")

    return session_length_sec


def print_settings(console, settings):
    """
    Print the available settings
    """
    console.print("--------------------------------", style="red")
    console.print("Settings", style="bold red")
    console.print(f"(1) Pomodoro: {settings[POMODORO]}", style="bold red")
    console.print(f"(2) Short break: {settings[SHORT_BREAK]}", style="bold red")
    console.print(f"(3) Long break: {settings[LONG_BREAK]}", style="bold red")
    console.print(
        f"(4) Sessions until each long break: {settings[SESSIONS_UNTIL_LONG]}",
        style="bold red",
    )
    console.print(f"(5) Auto start sessions: {settings[AUTO_START]}", style="bold red")
    console.print("(0) Return to menu", style="bold red")
    console.print("--------------------------------", style="red")


def get_user_input(console):
    """
    Function for getting user input with error handling
    """
    choice = 0
    again = True
    while again:
        try:
            choice = int(console.input("[bold red]:[/] "))
            again = False
        except ValueError:
            console.print("Input must be an integer", style="bold red")

    return choice


def view_settings(console, settings):
    """
    Display the settings and allow for changes to be made
    """
    print_settings(console, settings)

    dict_string = ""
    again = True
    while again:
        try:
            choice = int(console.input("[bold red]:[/] "))
            if choice < 0 or choice > 5:
                continue
            elif choice == 0:
                break
            elif choice == 1:
                console.print("New pomodoro time (max of 150 mins.)", style="red bold")
                dict_string = POMODORO
            elif choice == 2:
                console.print(
                    "New short break time (max of 20 mins.)", style="red bold"
                )
                dict_string = SHORT_BREAK
            elif choice == 3:
                console.print("New long break time (max of 40 mins.)", style="red bold")
                dict_string = LONG_BREAK
            elif choice == 4:
                console.print(
                    "New number of sessions until each long break (max of 10)",
                    style="red bold",
                )
                dict_string = SESSIONS_UNTIL_LONG
            elif choice == 5:
                console.print("Auto start sessions (y or n)", style="red bold")
                yes_or_no = input()
                if yes_or_no.lower() == "y":
                    settings[AUTO_START] = True
                elif yes_or_no.lower() == "n":
                    settings[AUTO_START] = False
                again = False
                continue

            again = False

            choice = get_user_input(console)
            settings[dict_string] = choice

        except ValueError:
            console.print("Input must be an integer", style="bold red")


def change_session(console):
    """
    Allow for changing the current session type and return the user's numerical choice
    """
    console.print("Change the current session type: ", style="red bold")
    console.print("(1) Pomodoro", style="red bold")
    console.print("(2) Short break", style="red bold")
    console.print("(3) Long break", style="red bold")
    console.print("(0) Return to menu", style="red bold")

    again = True
    while again:
        choice = get_user_input(console)
        if choice >= 0 and choice <= 3:
            return choice - 1


def init_db():
    """
    Initialize and return database object
    """
    db = TinyDB("db.json")
    if not db.all():
        # Set default settings for first-time user
        db.insert(
            {
                "name": DEFAULT_USERNAME,
                "settings": {
                    "pomodoro": DEFAULT_POMODORO,
                    "short_break": DEFAULT_SHORT_BREAK,
                    "long_break": DEFAULT_LONG_BREAK,
                    "sessions_until_long": DEFAULT_SESSIONS_UNTIL_LONG,
                    "auto_start": DEFAULT_AUTO_START,
                },
                "total_time_studied": 0,
                "days": [],
            }
        )
    return db


def next_session(user, today_stats):
    """
    Change to the next session type
    """
    if (
        today_stats[CURRENT_SESSION_TYPE] == SHORT_BREAK
        or today_stats[CURRENT_SESSION_TYPE] == LONG_BREAK
    ):  # If it is a break session then next session is pomodoro
        today_stats[CURRENT_SESSION_TYPE] = POMODORO
    elif (
        today_stats[CURRENT_SESSION_TYPE] == POMODORO
    ):  # Pomodoro session is proceeded by either a short or long break
        if (
            today_stats[CURRENT_SESSION_NUM] % (user[SETTINGS][SESSIONS_UNTIL_LONG])
            == 0
        ):
            today_stats[CURRENT_SESSION_TYPE] = LONG_BREAK
        else:
            today_stats[CURRENT_SESSION_TYPE] = SHORT_BREAK
        today_stats[CURRENT_SESSION_NUM] += 1


def view_stats(console, user, today_stats):
    """
    Print overall and daily statistics
    """
    console.print("Overall Statistics: ", style="red bold")
    console.print(
        f"Total Time Studied: {timedelta(seconds = user[TOTAL_TIME_STUDIED] + today_stats[TOTAL_TIME_STUDIED])}\n",
        style="red bold",
    )
    table = Table(title="Daily Statistics")
    table.add_column("Date", justify="center", style="cyan", no_wrap=True)
    table.add_column("Time Studied", justify="center", style="magenta")
    table.add_column("Sessions Completed", justify="center", style="green")
    for day in user[DAYS]:
        table.add_row(
            str(day[DATE]),
            str(timedelta(seconds=day[TIME_STUDIED])),
            str(day[SESSIONS_COMPLETED]),
        )
    table.add_row(
        "Current",
        str(timedelta(seconds=today_stats[TOTAL_TIME_STUDIED])),
        str(today_stats[CURRENT_SESSION_NUM] - 1),
    )
    console.print(table)


def replace_underscore(input: str):
    return input.replace("_", " ")


def get_session_type(input: int):
    if input == 0:
        return POMODORO
    elif input == 1:
        return SHORT_BREAK
    elif input == 2:
        return LONG_BREAK
    return INVALID


def main():
    db = init_db()

    """
    Initialize variables
    """
    console = Console(width=40)
    cursor.hide()
    # Get the first item in the database (there should only be one item)
    user = db.all()[0]
    today_stats = {
        "current_session_type": POMODORO,
        "current_session_num": 1,
        "total_time_studied": 0,
    }
    choice = 0

    while True:
        """
        Print main menu information after each session or when returning from another menu
        """
        console.print("Pomodoro Timer", style="dark_slate_gray2 on red", justify="left")
        console.print("--------------------------------", style="red")
        console.print(
            f"Current session: {replace_underscore(today_stats[CURRENT_SESSION_TYPE])}",
            style="bold red",
        )
        # Only show session number when it is a pomodoro session
        if today_stats[CURRENT_SESSION_TYPE] == POMODORO:
            console.print(
                f"Session #{today_stats[CURRENT_SESSION_NUM]}", style="bold red"
            )
        console.print(
            f"Session length: {user[SETTINGS][today_stats[CURRENT_SESSION_TYPE]]} minutes",
            style="bold red",
        )
        console.print(
            f"Total time studied: {timedelta(seconds = today_stats[TOTAL_TIME_STUDIED])}",
            style="bold red",
        )
        console.print("--------------------------------", style="red")
        console.print("Press 1 to start session.", style="red bold")
        console.print("Press 2 to adjust settings.", style="red bold")
        console.print("Press 3 to change current session.", style="red bold")
        console.print("Press 4 to see your stats.", style="red bold")
        console.print("Press 0 to quit.", style="red bold")

        again = True
        while again:
            choice = get_user_input(console)
            if choice >= 0 and choice <= 4:
                again = False

        """
        Perform action depending on user's main menu input
        """
        if choice == 1:  # Start session
            restart = True
            while restart:  # Start sessions automatically
                session_time_studied = start_timer(
                    console,
                    user[SETTINGS][today_stats[CURRENT_SESSION_TYPE]] * 60,
                )
                if (
                    today_stats[CURRENT_SESSION_TYPE] == POMODORO
                ):  # Only add session time if it is the pomodoro session
                    today_stats[TOTAL_TIME_STUDIED] += session_time_studied

                if (
                    session_time_studied
                    < user[SETTINGS][today_stats[CURRENT_SESSION_TYPE]] * 60
                    or user[SETTINGS][AUTO_START] is False
                ):  # Don't auto start
                    restart = False
                    continue
                next_session(user, today_stats)  # Change session
                console.print(
                    f"Current session: {replace_underscore(today_stats[CURRENT_SESSION_TYPE])}",
                    style="bold red",
                )
        elif choice == 2:  # View settings
            view_settings(console, user[SETTINGS])
            continue
        elif choice == 3:  # View session change
            new_session = get_session_type(change_session(console))
            if new_session != INVALID:
                today_stats[CURRENT_SESSION_TYPE] = new_session
            continue
        elif choice == 4:  # View statistics
            view_stats(console, user, today_stats)
            continue
        elif choice == 0:  # Exit program
            # Track time studied across all program runs
            user[TOTAL_TIME_STUDIED] += today_stats[TOTAL_TIME_STUDIED]
            today = date.today().strftime("%m/%d/%y")
            element = None

            for day in user[DAYS]:  # Look for today's date to update the data
                if day[DATE] == today:
                    element = day

            if element:  # If data for today exists
                program_run_data = {
                    "date": element[DATE],
                    "time_studied": element[TIME_STUDIED]
                    + today_stats[TOTAL_TIME_STUDIED],
                    "sessions_completed": element[SESSIONS_COMPLETED]
                    + today_stats[CURRENT_SESSION_NUM]
                    - 1,
                }
                # Remove the previous data for today
                user[DAYS].pop()
            else:  # If this is the first data for today
                program_run_data = {
                    "date": today,
                    "time_studied": today_stats[TOTAL_TIME_STUDIED],
                    "sessions_completed": today_stats[CURRENT_SESSION_NUM] - 1,
                }

            # Add the data for today to data for all days
            user[DAYS].append(program_run_data)
            User = Query()
            db.update(user, User.name == DEFAULT_USERNAME)  # Update the database
            sys.exit(0)  # Exit the program

        # Change the current session and update the session number
        next_session(user, today_stats)


if __name__ == "__main__":
    main()  # Start of program
