from rich.console import Console
from rich.table import Table
from datetime import timedelta, date
from tinydb import TinyDB, Query
import time
import sys
import cursor
from user import (
    User,
    Settings,
    Run,
    Day,
    DEFAULT_USERNAME,
    POMODORO,
    SHORT_BREAK,
    LONG_BREAK,
)


def show_time_left(console: Console, time_left: int):
    """
    Function called every second timer is active
    """
    console.print(f"{time_left}", end="\r")


def start_timer(console: Console, session_length_sec: int):
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


def print_settings(console: Console, settings: Settings):
    """
    Print the available settings
    """
    console.print("--------------------------------", style="red")
    console.print("Settings", style="bold red")
    console.print(f"(1) Pomodoro: {settings.pomodoro}", style="bold red")
    console.print(f"(2) Short break: {settings.short_break}", style="bold red")
    console.print(f"(3) Long break: {settings.long_break}", style="bold red")
    console.print(
        f"(4) Sessions until each long break: {settings.sessions_until_long}",
        style="bold red",
    )
    console.print(f"(5) Auto start sessions: {settings.auto_start}", style="bold red")
    console.print("(0) Return to menu", style="bold red")
    console.print("--------------------------------", style="red")


def get_user_input(console: Console):
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


def view_settings(console: Console, settings: Settings):
    """
    Display the settings and allow for changes to be made
    """
    print_settings(console, settings)

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
                value = get_user_input(console)
                settings.pomodoro = value
            elif choice == 2:
                console.print(
                    "New short break time (max of 20 mins.)", style="red bold"
                )
                value = get_user_input(console)
                settings.short_break = value
            elif choice == 3:
                console.print("New long break time (max of 40 mins.)", style="red bold")
                value = get_user_input(console)
                settings.long_break = value
            elif choice == 4:
                console.print(
                    "New number of sessions until each long break (max of 10)",
                    style="red bold",
                )
                value = get_user_input(console)
                settings.sessions_until_long = value
            elif choice == 5:
                console.print("Auto start sessions (y or n)", style="red bold")
                yes_or_no = input()
                if yes_or_no.lower() == "y":
                    settings.auto_start = True
                elif yes_or_no.lower() == "n":
                    settings.auto_start = False

            again = False

        except ValueError:
            console.print("Input must be an integer", style="bold red")


def change_session(console: Console):
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
        db.insert(User())
    return db


def next_session(user: User, run: Run):
    """
    Change to the next session type
    """
    if (
        run.current_session_type == SHORT_BREAK
        or run.current_session_type == LONG_BREAK
    ):  # If it is a break session then next session is pomodoro
        run.current_session_type = POMODORO
    elif (
        run.current_session_type == POMODORO
    ):  # Pomodoro session is proceeded by either a short or long break
        if run.current_session_num % (user.settings.sessions_until_long) == 0:
            run.current_session_type = LONG_BREAK
        else:
            run.current_session_type = SHORT_BREAK
        run.current_session_num += 1


def view_stats(console: Console, user: User, run: Run):
    """
    Print overall and daily statistics
    """
    console.print("Overall Statistics: ", style="red bold")
    console.print(
        f"Total Time Studied: {timedelta(seconds = user.total_time_studied + run.total_time_studied)}\n",
        style="red bold",
    )
    table = Table(title="Daily Statistics")
    table.add_column("Date", justify="center", style="cyan", no_wrap=True)
    table.add_column("Time Studied", justify="center", style="magenta")
    table.add_column("Sessions Completed", justify="center", style="green")
    for day in user.days:
        table.add_row(
            str(day.date),
            str(timedelta(seconds=day.time_studied)),
            str(day.sessions_completed),
        )
    table.add_row(
        "Current",
        str(timedelta(seconds=run.total_time_studied)),
        str(run.current_session_num - 1),
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
    return "invalid"


def main():
    db = init_db()

    """
    Initialize variables
    """
    console = Console(width=40)
    cursor.hide()
    # Get the first item in the database (there should only be one item)
    data = db.all()[0]
    user = User()
    user.set_values(data)
    run = Run()
    choice = 0

    while True:
        """
        Print main menu information after each session or when returning from another menu
        """
        console.print("Pomodoro Timer", style="dark_slate_gray2 on red", justify="left")
        console.print("--------------------------------", style="red")
        console.print(
            f"Current session: {replace_underscore(run.current_session_type)}",
            style="bold red",
        )
        # Only show session number when it is a pomodoro session
        if run.current_session_type == POMODORO:
            console.print(f"Session #{run.current_session_num}", style="bold red")
        console.print(
            f"Session length: {user.get_session_length(run.current_session_type)} minutes",
            style="bold red",
        )
        console.print(
            f"Total time studied: {timedelta(seconds = run.total_time_studied)}",
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
                    user.get_session_length(run.current_session_type) * 60,
                )
                if (
                    run.current_session_type == POMODORO
                ):  # Only add session time if it is the pomodoro session
                    run.total_time_studied += session_time_studied

                if (
                    session_time_studied
                    < user.get_session_length(run.current_session_type) * 60
                    or user.settings.auto_start is False
                ):  # Don't auto start
                    restart = False
                    continue
                next_session(user, run.current_session_type)  # Change session
                console.print(
                    f"Current session: {replace_underscore(run.current_session_type)}",
                    style="bold red",
                )
        elif choice == 2:  # View settings
            view_settings(console, user.settings)
            continue
        elif choice == 3:  # View session change
            new_session = get_session_type(change_session(console))
            if new_session != "invalid":
                run.current_session_type = new_session
            continue
        elif choice == 4:  # View statistics
            view_stats(console, user, run)
            continue
        elif choice == 0:  # Exit program
            # Track time studied across all program runs
            user.total_time_studied += run.total_time_studied
            today = date.today().strftime("%m/%d/%y")
            day_obj = None

            for day in user.days:  # Look for today's date to update the data
                if day.date == today:
                    day_obj = day

            if day_obj:  # If data for today exists
                program_run_data = {
                    "date": day_obj.date,
                    "time_studied": day_obj.time_studied + run.total_time_studied,
                    "sessions_completed": day_obj.sessions_completed
                    + run.current_session_num
                    - 1,
                }
                # Remove the previous data for today
                user.days.pop()
            else:  # If this is the first data for today
                program_run_data = {
                    "date": today,
                    "time_studied": run.total_time_studied,
                    "sessions_completed": run.current_session_num - 1,
                }

            # Add the data for today to data for all days
            new_day = Day()
            new_day.set_values(program_run_data)
            user.days.append(new_day)
            # Update the database
            db.update(user.get_dict(), Query().name == DEFAULT_USERNAME)
            sys.exit(0)  # Exit the program

        # Change the current session and update the session number
        next_session(user, run)


if __name__ == "__main__":
    main()  # Start of program
