from rich.console import Console
from rich.progress import Progress
from rich.text import Text
from datetime import datetime
from datetime import timedelta
from win10toast import ToastNotifier
import sched, time
import sys

"""
In development.

To do:
-Error handling
-Stylize text
-Keep track of total time spent studying
-Store in a database using sqlite3?
-Add option to auto start next session
"""

def showTimeLeft(time_left):
    sys.stdout.write("\r%s" % format(time_left))

def startTimer(console, current_session_type):
    startAt = current_session_type * 60
    #now = datetime.now().time()
    #t2 = now.strftime("%M:%S")
    #starttime = time.time()
    """
    with Progress() as progress:
        task1 = progress.add_task("Studying...", total=1500)
        while not progress.finished:
            progress.update(task1, advance=0.5)
            time.sleep(1.0)
    """
    valid = 1
    while(valid != 0):
        try:
            while startAt >= 0:
                t1 = timedelta(seconds = startAt)
                showTimeLeft(t1)
                startAt -= 1
                time.sleep(1.0)
            valid = 0
            print("")
        except KeyboardInterrupt:
            print("\nTime interrupted!")
            print("(1) Continue")
            print("(2) Finish early")
            option = int(input())
            if(option == 2):
                return
                
    console.print("Time is up!", style="bold red")
    toast = ToastNotifier()
    toast.show_toast("Cli-Pomodoro", "Your session has finished!", duration=5)

def printSettings(console, settings):
    console.print("--------------------------------", style="red")
    print("Settings")
    print("(1) Pomodoro: {}".format(settings["pomodoro"]))
    print("(2) Short break: {}".format(settings["short_break"]))
    print("(3) Long break: {}".format(settings["long_break"]))
    print("(4) Sessions until each long break: {}".format(settings["sessions_until_long"]))
    print("(0) Return to menu")
    console.print("--------------------------------", style="red")

def viewSettings(console, settings):
    printSettings(console, settings)
    choice = int(input(": "))
    if(choice == 1):
        choice = int(input("New pomodoro time (max of 150 mins.): "))
        settings["pomodoro"] = choice
    elif(choice == 2):
        choice = int(input("New short break time (max of 20 mins.): "))
        settings["short_break"] = choice
    elif(choice == 3):
        choice = int(input("New short break time (max of 40 mins.): "))
        settings["long_break"] = choice
    elif(choice == 4):
        choice = int(input("New number of sessions until each long break (max of 10): "))
        settings["sessions_until_long"] = choice

def changeSession(console):
    print("Change the current session type: ")
    print("(1) Pomodoro")
    print("(2) Short break")
    print("(3) Long break")
    choice = int(input())
    return choice


def main():
    console = Console()
    choice = 0
    settings = {
        "pomodoro": 25,
        "short_break": 5,
        "long_break": 10,
        "sessions_until_long": 4,
    }
    sessions = ['pomodoro', 'short_break', 'long_break']
    current_session_type = 0
    while True:
        console.print("Pomodoro Timer", style="bold red")
        console.print(f"Current session: {sessions[current_session_type].strip('_')}", style="bold red")
        console.print(f"Session length: {settings[sessions[current_session_type]]} minutes", style="bold red")
        console.print("--------------------------------", style="red")
        console.print("Press 1 to start the session.", style="red bold")
        console.print("Press 2 to adjust settings.", style="red bold")
        console.print("Press 3 to change current session.", style="red bold")
        console.print("Press 0 to quit.", style="red bold")
        choice = int(input())
        if(choice == 1):
            startTimer(console, settings[sessions[current_session_type]])
        elif(choice == 2):
            viewSettings(console, settings)
        elif(choice == 3):
            new_session = changeSession(console)
            current_session_type = new_session - 1
            continue
        elif(choice == 0):
            sys.exit(0)

        if(current_session_type >= len(sessions) - 1):
            current_session_type = 0
        else:
            current_session_type += 1


if __name__ == '__main__':
    main()