from rich.console import Console
from rich.progress import Progress
from rich.text import Text
from rich.table import Table
from datetime import datetime, timedelta, date
from tinydb import TinyDB, Query
import sched, time
import sys
import cursor

OS_WINDOWS = False
if sys.platform.startswith("win32") or sys.platform.startswith("cygwin"):
    OS_WINDOWS = True
    from win10toast_click import ToastNotifier

"""
To do:
-Add tasks
-Refactor code
"""

def showTimeLeft(console, time_left):
    """
    Function called every second timer is active
    """
    console.print(f"{time_left}", end = "\r")

def startTimer(console, session_length):
    """
    Function for running the timer
    """
    time_left_seconds = session_length * 60

    # Run the timer until the timer hits zero or user signal to stop
    active = True
    while(active):
        try:
            # Update the timer and print the time to the terminal
            while time_left_seconds >= 0:
                time_left = timedelta(seconds = time_left_seconds) # Convert seconds into timedelta object
                showTimeLeft(console, time_left) # Print time left
                time.sleep(1.0) # Wait a second to update time
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
            while(again):
                option = getUserInput(console)

                # User input of 1 to continue timer and 2 to end timer
                if(option == 1):
                    again = False
                elif(option == 2):
                    return session_length * 60 - time_left_seconds
                
    # Notification that the timer is up
    console.print("Time is up!", style="bold red")
    if OS_WINDOWS:
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
    console.print(f"(5) Auto start sessions: {settings['auto_start']}", style="bold red")
    console.print("(0) Return to menu", style="bold red")
    console.print("--------------------------------", style="red")

def getUserInput(console):
    """
    Function for getting user input with error handling
    """
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
            if(choice < 0 or choice > 5):
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
            elif(choice == 5):
                console.print("Auto start sessions (y or n)", style="red bold")
                yes_or_no = input()
                if(yes_or_no.lower() == 'y'):
                    settings['auto_start'] = True
                elif(yes_or_no.lower() == 'n'):
                    settings['auto_start'] = False
                again = False
                continue

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
        choice = getUserInput(console)
        if(choice >= 0 and choice <= 3):
            return choice

def initializeDatabase():
    """
    Initialize and return database object
    """
    db = TinyDB('db.json')
    if(not db.all()): # If first-time user
        db.insert({
            "name": "base_user",
            "settings": {
                "pomodoro": 25,
                "short_break": 5,
                "long_break": 10,
                "sessions_until_long": 4,
                "auto_start": False
            },
            "total_time_studied": 0,
            "days": []
        })
    return db

def nextSession(user, today_stats):
    """
    Change to the next session type
    """
    if(today_stats["current_session_type"] == 1 or today_stats["current_session_type"] == 2): # If it is a break session
        today_stats["current_session_type"] = 0
    elif(today_stats["current_session_type"] == 0): # If it is a pomodoro session
        if(today_stats["current_session_num"] % (user["settings"]["sessions_until_long"]) == 0):
            today_stats["current_session_type"] = 2
        else:
            today_stats["current_session_type"] = 1
        today_stats["current_session_num"] += 1

def viewStatistics(console, user, today_stats):
    """
    Print overall and daily statistics
    """
    console.print("Overall Statistics: ", style="red bold")
    console.print(f"Total Time Studied: {timedelta(seconds = user['total_time_studied'] + today_stats['total_time_studied'])}\n", style="red bold")
    table = Table(title="Daily Statistics")
    table.add_column("Date", justify="center", style="cyan", no_wrap=True)
    table.add_column("Time Studied", justify="center", style="magenta")
    table.add_column("Sessions Completed", justify="center", style="green")
    for day in user['days']:
        table.add_row(
            str(day['date']), 
            str(timedelta(seconds = day['time_studied'])), 
            str(day['sessions_completed'])
        )
    table.add_row(
        "Current", 
        str(timedelta(seconds = today_stats['total_time_studied'])), 
        str(today_stats['current_session_num'] - 1)
    )
    console.print(table)

def main():
    db = initializeDatabase()

    """
    Initialize variables 
    """
    console = Console(width=40)
    cursor.hide()
    user = db.all()[0]  # Get the first item in the database (there should only be one item)
    session_types = ['pomodoro', 'short_break', 'long_break']
    today_stats = {
        "current_session_type": 0,  # 0 - pomodoro, 1 - short break, 2 - long break
        "current_session_num": 1,
        "total_time_studied": 0
    }
    choice = 0

    while True: 
        """
        Print main menu information after each session or when returning from another menu
        """
        console.print("Pomodoro Timer", style="dark_slate_gray2 on red", justify="left")
        console.print("--------------------------------", style="red")
        console.print(f"Current session: {session_types[today_stats['current_session_type']].replace('_', ' ')}", style="bold red")
        if(today_stats['current_session_type'] == 0): #Only show session number when it is a pomodoro session
            console.print(f"Session #{today_stats['current_session_num']}", style="bold red")
        console.print(f"Session length: {user['settings'][session_types[today_stats['current_session_type']]]} minutes", style="bold red")
        console.print(f"Total time studied: {timedelta(seconds = today_stats['total_time_studied'])}", style="bold red")
        console.print("--------------------------------", style="red")
        console.print("Press 1 to start session.", style="red bold")
        console.print("Press 2 to adjust settings.", style="red bold")
        console.print("Press 3 to change current session.", style="red bold")
        console.print("Press 4 to see your stats.", style="red bold")
        console.print("Press 0 to quit.", style="red bold")
        
        again = True
        while(again):
            choice = getUserInput(console)
            if(choice >= 0 and choice <= 4):
                again = False

        """
        Perform action depending on user's main menu input
        """
        if(choice == 1): # Start session
            restart = True
            while(restart): # Start sessions automatically
                session_time_studied = startTimer(console, user['settings'][session_types[today_stats["current_session_type"]]])
                if(today_stats["current_session_type"] == 0): # Only add session time if it is the pomodoro session
                    today_stats["total_time_studied"] += session_time_studied

                if(session_time_studied < user['settings'][session_types[today_stats["current_session_type"]]] * 60
                    or user['settings']['auto_start'] == False): # Don't auto start
                    restart = False
                    continue
                nextSession(user, today_stats) # Change session
                console.print(f"Current session: {session_types[today_stats['current_session_type']].replace('_', ' ')}", style="bold red")
        elif(choice == 2): # View settings
            viewSettings(console, user['settings'])
            continue
        elif(choice == 3): # View session change
            new_session = changeSession(console)
            if(new_session >= 1 and new_session <= 3):
                today_stats["current_session_type"] = new_session - 1
            continue
        elif(choice == 4): # View statistics
            viewStatistics(console, user, today_stats)
            continue
        elif(choice == 0): # Exit program
            user['total_time_studied'] += today_stats["total_time_studied"] # Track time studied across all program runs
            today = date.today().strftime("%m/%d/%y")
            element = None
            
            for day in user['days']: # Look for today's date to update the data
                if(day['date'] == today):
                    element = day

            if(element): # If data for today exists
                program_run_data = {
                    "date": element['date'],
                    "time_studied": element['time_studied'] + today_stats["total_time_studied"],
                    "sessions_completed": element['sessions_completed'] + today_stats["current_session_num"] - 1
                }
                user['days'].pop(len(user['days'])-1) # Remove the previous data for today
            else: # If this is the first data for today
                program_run_data = {
                    "date": today,
                    "time_studied": today_stats["total_time_studied"],
                    "sessions_completed": today_stats["current_session_num"] - 1
                }

            user['days'].append(program_run_data) # Add the data for today to data for all days
            User = Query()
            db.update(user, User.name == 'base_user') # Update the database
            sys.exit(0) # Exit the program

        nextSession(user, today_stats) # Change the current session and update the session number

if __name__ == '__main__':
    main() # Start of program