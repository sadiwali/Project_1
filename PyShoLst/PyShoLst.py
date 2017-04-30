# Copyright Sadi M. Wali, 2017
# Distributed under the terms of the GNU General Public License.
#
# This file is part of Simple Shift Manager program
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this file.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
import os


import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime

# for clearing console
clear = lambda: os.system('cls')


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'UNOFFICIAL_GAP_BLOOR_SCHEDULE_MANAGER_APP'



class schedule():
    # Representation Invariant:
    # self.days is a list of length 7
    # self.days[0] is Sunday, self.days[-1] is Saturday

    # each item in self.days is a 3-tuple in following format:
    #   ('title', (start_time, end_time), (formatted_start_time, formatted_end_time))
    # self.name is beginning month, and date number in zero-format joined with '-' and end month, date number in zero-format
    # self.year is current year

    # global vars:

    # days of the week, Sunday is first day
    days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    # line shifting
    next_date_shifter = 4

    def __init__(self: 'schedule') -> None:
        ''' Initializes the schedule class.

        REQ: None
        '''
        # for storing the seperated days
        self.days = {}
        self.year = str(datetime.datetime.now().year)
        self.name = ''
        # process the text into seperate days
        self.days = self.process_file()


    def get_hours(self: 'schedule') -> int:
        ''' Returns the number of hours in current week's schedule.

        REQ: schedule properly implemented
        '''

        # storing number of total hours
        hours = 0

        # loop through each day and add up hours
        for day in self.days:
            # only collect hours if day is working, not Off
            if self.days[day] != '':
                # specify the start and end times
                start_hours = self.days[day][1][0]
                end_hours = self.days[day][1][1]
                    
                # convert to cent format
                start_hours = int(start_hours[0:2]) + int(start_hours[2:4]) / 60.0
                end_hours = int(end_hours[0:2]) + int(end_hours[2:4]) / 60.0
                
                # subtract end from start using the cent format
                hours += end_hours - start_hours
        # return the int # of total hours
        return hours

    def get_year() -> str:
        ''' Return the year of schedule
        '''
        return self.year


    def process_file(self: 'schedule') -> dict:
        ''' Returns a dict containing the appropriate timing schedules
        according to each day. Items in list are 3-tuples where first element is
        title of job, second element is time in military format, third element is
        formatted times in RFC3339 format.

        REQ: None
        '''
        
        # read the file
        with open('file.txt') as file:
            lines = file.read().splitlines()

        # dict to be returned
        dict_to_ret = {}

        # initialize the dict with days of week
        for day in self.days_of_week:
            dict_to_ret[day] = ''

        # first and last day month-formats
        first_day = ''
        last_day = ''
            
        # look through each line and process
        for i in range(len(lines)):

            # check if line not empty, and day is a working day (time is given)
            if bool(lines[i]) and lines[i][0].isnumeric():


                # previous line is working day
                # next line is title
                line_working_day = lines[i - 1]
                line_working_title = lines[i + 1]
                # time is a tuple containing string times in 24-h format
                time = self._process_time(lines[i])

                # for use in calendar insertion
                formatted_start_time = (self.year + '-' + 
                                  line_working_day[line_working_day.index(',') + 2:line_working_day.index(',') + 4] + '-' +
                                  line_working_day[line_working_day.index(',') + 5: line_working_day.index(',') + 9] + 'T' +
                                  time[0][0:2] + ':' + time[0][2:4] + ':00-04:00')
                # same format as start time, but with [1] index for end_time
                formatted_end_time = (self.year + '-' + 
                                  line_working_day[line_working_day.index(',') + 2:line_working_day.index(',') + 4] + '-' +
                                  line_working_day[line_working_day.index(',') + 5: line_working_day.index(',') + 9] + 'T' +
                                  time[1][0:2] + ':' + time[1][2:4] + ':00-04:00')
                # set the start date and end date
                # first day is only set when initially empty string
                if first_day == '':
                    first_day =  (line_working_day[line_working_day.index(',') + 2:line_working_day.index(',') + 4] + '-' +
                                  line_working_day[line_working_day.index(',') + 5: line_working_day.index(',') + 9])
                # continuously update last day until end of loop
                last_day = (line_working_day[line_working_day.index(',') + 2:line_working_day.index(',') + 4] + '-' +
                            line_working_day[line_working_day.index(',') + 5: line_working_day.index(',') + 9])

                # find the dicitonary key with name of day, set to 3-tuple (title, line_time, formatted_time)
                dict_to_ret[line_working_day[0: line_working_day.index(',')]] = (line_working_title, time, (formatted_start_time, formatted_end_time))
                # increment i to next day
                i += self.next_date_shifter
                    
        # set schedule title (start and finish dates)
        self.name = first_day + ' to ' + last_day
        # return the new dictionary
        return dict_to_ret

    def _process_time(self: 'schedule', in_str: 'str') -> (str, str):
        ''' Returns tuple containing start, finish military time.
        Example given format: 03:00PM - 09:00PM  WRK

        REQ: in_str is valid time format from email
    
        '''
        

        # caclualte the start time with 1200 hours considered
        # PM
        if in_str[5] == 'P':
            # check if noon, no need to add 1200
            if in_str[0:2] == '12':
                start_time = in_str[0:2] + in_str[3:5]
            else:
                start_time = str(int(in_str[0:2] + in_str[3:5]) + 1200)

        # AM
        elif in_str[5] == 'A':
            # check if midnight 12:xxAM, convert to 00 hours
            if in_str[0:2] == '12':
                start_time = '00' + in_str[3:5]
            else:
                start_time = in_str[0:2] + in_str[3:5]
        
        # calculate the end time    
        # PM 
        if in_str[15] == 'P':
            if in_str[10:12] == '12':
                end_time = in_str[10:12] + in_str[13:15]
            else:
                end_time = str(int(in_str[10:12] + in_str[13:15]) + 1200)

        # AM
        elif in_str[15] == 'A':
            if in_str[10:12] == '12':
                end_time = '00' + in_str[13:15]
            else:
                end_time = in_str + in_str[13:15]
        # return the new time in format: ('1200', '1200')
        return (start_time, end_time)

def main() -> None:
    ''' Initializes the schedule class, and displays the proper menues
    '''
    s1 = schedule()
    # display the main menu at beginning
    disp_main_menu(s1)

def disp_main_menu(schedule: 'schedule') -> None:
    ''' Displays the main menu prompt, and awaits proper
    input from user.
    '''
    print('currently loaded schedule for (Sunday -> Saturday) ' + schedule.name )
    print("Please select an option:")
    print('(1) Display your schedule')
    print('(2) Get total hours this week')
    print('(3) Export to calendar')
    print('(4) Give away a shift')
    print('(5) Close')

    # default input to initiate loop at least once
    inp = 'null'
    



    while inp == '' or inp not in '12345':
      
        inp = input()
        print(inp)
        # clear the console
        clear()

    # correct input found, begin processing
    if inp == '1':
        disp_schedule(schedule)
    elif inp == '2':
        disp_hours(schedule)
    elif inp == '3':
        act_export_cal(schedule)
    elif inp == '4':
        act_shift_messenger(schedule)
    elif inp == '5':
        close()
    

def disp_schedule(schedule: 'schedule') -> None:
    ''' Given a schedule, displays the events formatted.
    '''
    for day in schedule.days:
        if schedule.days[day] != '':
            print('"' + schedule.days[day][0] + '" ' + day + ' ' + schedule.days[day][2][0][5:10] + ' ' + schedule.days[day][1][0] + ' to ' + schedule.days[day][1][1])
    # display back menu prompt
    disp_back_menu(schedule)
        
def disp_hours(schedule: 'schedule') -> None:
    ''' Displays the number of hours worked in current week
    '''
    # clear the screen,
    clear()
    # print the hours worked
    print('For the current week, you are working ' + str(schedule.get_hours()) + ' hours')
    disp_back_menu(schedule)

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'simple_shift_manager.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def act_export_cal(schedule: 'schedule') -> None:
    """ Exports all work events to Google Calendar.
    """
    # set up the calendar API
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    # counter of work days
    w_day_counter = 0
    
    # loop through each day, and if event exists, add to calendar
    for day in schedule.days:
        if schedule.days[day] != '':
            # get details about event
            # first item in 3-tuple is title
            title = schedule.days[day][0]
            # start time, end time
            # third item in 3-tuple is 2-tuple containing formatted start, end time
            start_time = schedule.days[day][2][0]
            end_time = schedule.days[day][2][1]
            
            # event shell
            event = {
              'summary': title,
              'location': '60 Bloor St W, Toronto, ON M4W',
              'description': '',
              'start': {
                'dateTime': start_time,
                'timeZone': 'America/Toronto',
              },
              'end': {
                'dateTime': end_time,
                'timeZone': 'America/Toronto',
              },          
              'reminders': {
                'useDefault': False,
                'overrides': [
                  {'method': 'popup', 'minutes': 60},
                ],
              },
            }

            # insert the event into Calendar
            event = service.events().insert(calendarId='primary', body=event).execute()

            # increment the number of work days aded to calendar
            w_day_counter += 1
            
            # confirmation
            # grammar formatting (singular or plural)
            if w_day_counter <= 1:
                print(str(w_day_counter) + ' event created')
            else:
                print(str(w_day_counter) + ' events created')
    # prints successfull
    print('All ' + str(w_day_counter) + ' events added to Calendar successfully')
    # go to main menu
    disp_back_menu(schedule)

def act_shift_messenger(schedule: 'schedule') -> None:
    ''' Utilizes the Shift Messenger api to post a shift to give away.
    '''
    print('this feature is not yet available')
    disp_back_menu(schedule)
            
def disp_back_menu(schedule: 'schedule') -> None:
    ''' Displays a 'go back to menu' prompt and awaits user input
    '''

    print("'b' to go back to main menu...")
    inp = 'null'

    while inp != 'b':
        # accept input
        inp = input()
        
        # if faulty input, display prompt again
        if inp != 'b':
            clear()
            disp_back_menu(schedule)

    # loop was exited because 'b', go back to menu after clearing screen
    clear()
    disp_main_menu(schedule)
            

    
# initialize the program
main()
