from rich.console import Console
from rich.progress import Progress
from rich.text import Text
from datetime import datetime, timedelta, date
from win10toast import ToastNotifier
from tinydb import TinyDB, Query
import sched, time
import sys
import cursor

"""
In development.

To do:
-Add tasks
-Organize data better
-Add option to auto start next session
"""

def showTimeLeft(console, time_left):
    console.print(f"{time_left}", end = "\r")

def startTimer(console, session_length):
    time_left_seconds = session_length * 60

    # with Progress() as progress:
    #     task1 = progress.add_task("Studying...", total=1500)
    #     while not progress.finished:
    #         progress.update(task1, advance=0.5)
    #         time.sleep(1.0)

    valid = 1
    while(valid != 0):
        try:
            while time_left_seconds >= 0:
                time_left = timedelta(seconds = time_left_seconds) # Convert seconds into timedelta object
                showTimeLeft(console, time_left) # Print time left
                time.sleep(1.0) # Wait a second to update time
                time_left_seconds -= 1
            valid = 0
            print("")
        except KeyboardInterrupt:
            console.print("\nTime paused!", style="bold red")
            console.print("(1) Continue", style="bold red")
            console.print("(2) Finish early", style="bold red")
            option = int(input())
            if(option == 2):
                return session_length * 60 - time_left_seconds
                
    console.print("Time is up!", style="bold red")
    toast = ToastNotifier()
    toast.show_toast("Cli-Pomodoro", "Your session has ended!", duration=5)

    return session_length * 60

def printSettings(console, settings):
    """
    Print the available settings
    """
    console.print("--------------------------------", style="red")
    console.print("Settings", style="bold red")
    console.print(f"(1) Pomodoro: {settings['pomodoro']}", style="bold red")
    console.print(f"(2) Short break: {settings['short_break']}", style="bold red")
    console.print(f"(3) Long break: {settings['long_break']}", style="bold red")
    console.print(f"(4) Sessions until each long break: {settings['sessions_until_long']}", style="bold red")
    console.print("(0) Return to menu", style="bold red")
    console.print("--------------------------------", style="red")

def getUserInput(console):
    choice = 0
    again = True
    while(again):
        try:
            choice = int(console.input("[bold red]:[/] "))
            again = False
        except ValueError:
            console.print("Input must be an integer", style="bold red")

    return choice

def viewSettings(console, settings):
    """
    Display the settings and allow for changes to be made
    """
    printSettings(console, settings)

    dict_string = ""
    again = True
    while(again):
        try:
            choice = int(console.input("[bold red]:[/] "))
            if(choice < 0 or choice > 4):
                continue
            elif(choice == 0):
                break
            elif(choice == 1):
                console.print("New pomodoro time (max of 150 mins.)", style="red bold")
                dict_string = "pomodoro"
            elif(choice == 2):
                console.print("New short break time (max of 20 mins.)", style="red bold")
                dict_string = "short_break"
            elif(choice == 3):
                console.print("New long break time (max of 40 mins.)", style="red bold")
                dict_string = "long_break"
            elif(choice == 4):
                console.print("New number of sessions until each long break (max of 10)", style="red bold")
                dict_string = "sessions_until_long"

            again = False
            
            choice = getUserInput(console)
            settings[dict_string] = choice
            
        except ValueError:
            console.print("Input must be an integer", style="bold red")

def changeSession(console):
    """
    Allow for changing the current session type and return the user's numerical choice
    """
    console.print("Change the current session type: ", style="red bold")
    console.print("(1) Pomodoro", style="red bold")
    console.print("(2) Short break", style="red bold")
    console.print("(3) Long break", style="red bold")
    console.print("(0) Return to menu", style="red bold")

    again = True
    while(again):
        try:
            choice = int(console.input("[bold red]:[/] "))
            if(choice >= 0 and choice <= 3):
                return choice
        except ValueError:
            console.print("Input must be an integer", style="bold red")

def initializeDatabase():
    db = TinyDB('db.json')
    data = db.all()
    if(not data): # If first-time user
        db.insert({
            "name": "base_user",
            "pomodoro": 25,
            "short_break": 5,
            "long_break": 10,
            "sessions_until_long": 4,
            "total_time_studied": 0,
            "days": []
        })
    return db

def main():
    db = initializeDatabase()

    """
    Initialize variables 
    """
    console = Console(width=40)
    cursor.hide()
    user = db.all()[0]  # Get the first item in the database (there should only be one item)
    session_types = ['pomodoro', 'short_break', 'long_break']
    current_session_type = 0  #0 - pomodoro, 1 - short break, 2 - long break
    current_session_num = 1
    total_time_studied = 0
    choice = 0

    while True: 
        """
        Print main menu information after each session or when returning from another menu
        """
        console.print("Pomodoro Timer", style="dark_slate_gray2 on red", justify="left")
        console.print("--------------------------------", style="red")
        console.print(f"Current session: {session_types[current_session_type].replace('_', ' ')}", style="bold red")
        if(current_session_type == 0): #Only show session number when it is a pomodoro session
            console.print(f"Session #{current_session_num}", style="bold red")
        console.print(f"Session length: {user[session_types[current_session_type]]} minutes", style="bold red")
        console.print(f"Total time studied: {timedelta(seconds = total_time_studied)}", style="bold red")
        console.print("--------------------------------", style="red")
        console.print("Press 1 to start session.", style="red bold")
        console.print("Press 2 to adjust settings.", style="red bold")
        console.print("Press 3 to change current session.", style="red bold")
        console.print("Press 0 to quit.", style="red bold")
        
        again = True
        while(again):
            try:
                choice = int(console.input("[bold red]:[/] "))
                if(choice >= 0 and choice <= 3):
                    again = False
            except ValueError:
                console.print("Input must be an integer", style="bold red")

        """
        Perform action depending on user's input
        """
        if(choice == 1):
            session_time_studied = startTimer(console, user[session_types[current_session_type]])
            if(current_session_type == 0): # Only add session time if it is the pomodoro session
                total_time_studied += session_time_studied
        elif(choice == 2):
            viewSettings(console, user)
            continue
        elif(choice == 3):
            new_session = changeSession(console)
            if(new_session >= 1 and new_session <= 3):
                current_session_type = new_session - 1
            continue
        elif(choice == 0):
            user['total_time_studied'] += total_time_studied # Track time studied across all program runs
            today = date.today().strftime("%m/%d/%y")
            element = None
            for session in user['days']: # Look for today's date to update the data
                if(session['date'] == today):
                    element = session
            print(element)
            if(element):
                program_run_data = {
                    "date": element['date'],
                    "time_studied": element['time_studied'] + total_time_studied,
                    "sessions_completed": element['sessions_completed'] + current_session_num - 1
                }
                user['days'].pop(len(user['days'])-1)
            else:
                program_run_data = {
                    "date": today,
                    "time_studied": total_time_studied,
                    "sessions_completed": current_session_num - 1
                }

            user['days'].append(program_run_data) # Track time studied during current program run
            User = Query()
            db.update(user, User.name == 'base_user')
            sys.exit(0)

        """
        Change the current session and update the session number
        """
        if(current_session_type == 1 or current_session_type == 2): # If it is a break session
            current_session_type = 0
        elif(current_session_type == 0): # If it is a pomodoro session
            if(current_session_num % (user["sessions_until_long"]) == 0):
                current_session_type = 2
            else:
                current_session_type = 1
            current_session_num += 1

if __name__ == '__main__':
    main()