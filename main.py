from rich.console import Console
from rich.progress import Progress
from rich.text import Text
from datetime import datetime
from datetime import timedelta
from win10toast import ToastNotifier
import sched, time
import sys
import cursor
from tinydb import TinyDB, Query

"""
In development.

To do:
-Error handling
-Keep track of total time spent studying
-Store study time and settings in a database using tinydb
-Add option to auto start next session
"""

def showTimeLeft(console, time_left):
    #sys.stdout.write("\r%s" % format(time_left))
    console.print("{}".format(time_left), end = "\r")

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
                showTimeLeft(console, t1)
                startAt -= 1
                time.sleep(1.0)
            valid = 0
            print("")
        except KeyboardInterrupt:
            console.print("\nTime paused!", style="bold red")
            console.print("(1) Continue", style="bold red")
            console.print("(2) Finish early", style="bold red")
            option = int(input())
            if(option == 2):
                return
                
    console.print("Time is up!", style="bold red")
    toast = ToastNotifier()
    toast.show_toast("Cli-Pomodoro", "Your session has finished!", duration=5)

def printSettings(console, settings):
    console.print("--------------------------------", style="red")
    console.print("Settings", style="bold red")
    console.print("(1) Pomodoro: {}".format(settings['pomodoro']), style="bold red")
    console.print("(2) Short break: {}".format(settings["short_break"]), style="bold red")
    console.print("(3) Long break: {}".format(settings["long_break"]), style="bold red")
    console.print("(4) Sessions until each long break: {}".format(settings["sessions_until_long"]), style="bold red")
    console.print("(0) Return to menu", style="bold red")
    console.print("--------------------------------", style="red")

def viewSettings(console, settings):
    printSettings(console, settings)
    choice = int(console.input("[bold red]:[/] "))
    if(choice == 1):
        console.print("New pomodoro time (max of 150 mins.)", style="red bold")
        choice = int(console.input("[bold red]:[/] "))
        settings["pomodoro"] = choice
    elif(choice == 2):
        console.print("New short break time (max of 20 mins.)", style="red bold")
        choice = int(console.input("[bold red]:[/] "))
        settings["short_break"] = choice
    elif(choice == 3):
        console.print("New long break time (max of 40 mins.)", style="red bold")
        choice = int(console.input("[bold red]:[/] "))
        settings["long_break"] = choice
    elif(choice == 4):
        console.print("New number of sessions until each long break (max of 10)", style="red bold")
        choice = int(console.input("[bold red]:[/] "))
        settings["sessions_until_long"] = choice

def changeSession(console):
    console.print("Change the current session type: ", style="red bold")
    console.print("(1) Pomodoro", style="red bold")
    console.print("(2) Short break", style="red bold")
    console.print("(3) Long break", style="red bold")
    console.print("(0) Return to menu", style="red bold")
    choice = int(console.input("[bold red]:[/] "))
    return choice


def main():
    console = Console(width=40)
    cursor.hide()
    choice = 0
    settings = {
        "pomodoro": 25,
        "short_break": 5,
        "long_break": 10,
        "sessions_until_long": 2,
    }
    sessions = ['pomodoro', 'short_break', 'long_break']
    current_session_type = 0
    current_session_num = 1
    while True:
        console.print("Pomodoro Timer", style="dark_slate_gray2 on red", justify="left")
        console.print("--------------------------------", style="red")
        console.print(f"Current session: {sessions[current_session_type].replace('_', ' ')}", style="bold red")
        if(current_session_type == 0):
            console.print(f"Session #{current_session_num}", style="bold red")
        console.print(f"Session length: {settings[sessions[current_session_type]]} minutes", style="bold red")
        console.print("--------------------------------", style="red")
        console.print("Press 1 to start session.", style="red bold")
        console.print("Press 2 to adjust settings.", style="red bold")
        console.print("Press 3 to change current session.", style="red bold")
        console.print("Press 0 to quit.", style="red bold")
        choice = int(console.input("[bold red]:[/] "))
        if(choice == 1):
            startTimer(console, settings[sessions[current_session_type]])
        elif(choice == 2):
            viewSettings(console, settings)
            continue
        elif(choice == 3):
            new_session = changeSession(console)
            if(new_session != 0):
                current_session_type = new_session - 1
            continue
        elif(choice == 0):
            sys.exit(0)

        if(current_session_type == 1 or current_session_type == 2):
            current_session_type = 0
        elif(current_session_type == 0 and current_session_num % (settings["sessions_until_long"] + 1) == 0):
            current_session_num += 1
            current_session_type = 2
        else:
            current_session_num += 1
            current_session_type = 1


if __name__ == '__main__':
    main()