import sched
import schedule 
import time
import datetime

def minutes_to_seconds( minutes: str ) -> int:
    #Converts minutes to seconds
    return int(minutes)*60

def hours_to_minutes( hours: str ) -> int:
    #Converts hours to minutesß
    return int(hours)*60

def hhmm_to_seconds( hhmm: str ) -> int:
    if hhmm != None:
        if len(hhmm.split(':')) != 2:
            print('Incorrect format. Argument must be formatted as HH:MM')
        return minutes_to_seconds(hours_to_minutes(hhmm.split(':')[0])) + \
            minutes_to_seconds(hhmm.split(':')[1])
    else:
        print('Incorrect format. Argument must be formatted as HH:MM')