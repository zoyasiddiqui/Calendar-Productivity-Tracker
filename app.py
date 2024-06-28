import datetime
import os.path
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from ttkthemes import ThemedTk
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import data

# declare global variables
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate():
    """
    This function does the initial authentication with the API
    """

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        except Exception:
            pass

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds

def main():
    # the root frame, declared with a theme
    root = ThemedTk(theme="breeze")

    # global variables
    global start_time
    global end_time
    start_time = None
    end_time = None

    global connection
    connection = data.main()

    global row_ctr
    global checkboxes
    global selected 

    def login():
        """
        This function will move users from the login page to the main page
        """
        try:
            creds = authenticate()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during authentication:\n{str(e)}")
            print(e)
            root.quit()

        # if authentication works, we move frames 
        login_button.pack_forget()
        login_frame.destroy()
        main_frame.pack(expand=True)
        welcome_label.grid(row=0, column=1, pady=10)
        instruction.grid(row=1, column=1, pady = 5)

        display(creds)
    
    def display(creds):
        """
        This function will do the initial work on the main page. Display the headings
        and display the buttons for all of the users calendars
        """
        #creating all the buttons
        service = build("calendar", "v3", credentials=creds)
        page_token = None # in case we have multiple pages of calendars
        all_cals = {}
        cal_btns = []
        while True:
            calendar_list = service.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                cal = calendar_list_entry['summary']
                all_cals[cal] = calendar_list_entry['id']
                cal_btns.append(ttk.Button(main_frame, text=cal, command=None))
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break
        
        #displaying all the buttons
        global row_ctr
        row_ctr = 2
        for b in cal_btns:
            category = b.cget("text")
            b.config(command=lambda cat=category: act(cat, service, all_cals))
            b.grid(row=row_ctr, column=0, pady = 5,stick="w")
            row_ctr += 1
            
        # intialize selected
        global selected
        selected = []

    def act(category, service, all_cals):
        """
        This function opens up the side panel (with the event title, start, end buttons, etc) once the user
        clicks on a calendar
        """
        _cleanup_checkboxes([], [])

        # display all the buttons and such in the right panel
        title = ttk.Entry(main_frame)
        title.insert(0, "Event Title")
        title.grid(row=2, column=2, padx=10, pady=5, stick="e")
        alert = ttk.Label(main_frame, text="Timer has started") #will show up when they click start
        start = ttk.Button(main_frame, text="Start", command=lambda: get_start_time(alert))
        end = ttk.Button(main_frame, text="End", command=lambda: wrapup(service, all_cals[category], category, title, alert))
        start.grid(row=3, column=2, padx=5, pady=5, stick="e")
        end.grid(row=4, column=2, padx=5, pady=5, stick="e")
        stats = ttk.Button(main_frame, text="See stats for this category", command=lambda: get_stats(category))
        stats.grid(row=6, column=2, padx=5, pady=10, stick="e")
        add = ttk.Button(main_frame, text="Add events for stats", command=lambda: display_events(service, all_cals[category], category, 0, "add"))
        add.grid(row=7, column=2, padx=5, pady=10, stick="e")
        delete = ttk.Button(main_frame, text="Delete events from stats", command=lambda: display_events(service, all_cals[category], category, 0, "del"))
        delete.grid(row=8, column=2, padx=5, pady=10, stick="e")

    def get_start_time(alert):
        """
        Record the time the user clicked "start", ie the start time of their task
        """
        _cleanup_checkboxes([], [])

        # do actual function work
        global start_time
        start_time = datetime.datetime.now(datetime.timezone.utc)
        hours_added = datetime.timedelta(hours=-7)
        start_time += hours_added

        print(start_time)

        alert.grid(row=5, column=2, padx=5, pady=5, stick="w") #tell users timer has started
    
    def wrapup(service, id, category, title, alert):
        """
        Put together JSON object and make API call to add event to calendar. Add to database as well. 
        """
        _cleanup_checkboxes([], [])
        
        global start_time
        global end_time
        global connection

        if start_time != None:
            end_time = datetime.datetime.now(datetime.timezone.utc)
            hours_added = datetime.timedelta(hours=-7)
            end_time += hours_added

            start_json = start_time.strftime("%Y-%m-%dT%H:%M:%S-07:00")
            end_json = end_time.strftime("%Y-%m-%dT%H:%M:%S-07:00")

            #adding the event to the user's google calendar with a json object
            event = {
                'summary': title.get(),
                'start': {
                    'dateTime': start_json,
                    'timeZone': 'America/Los_Angeles',
                },
                'end': {
                    'dateTime': end_json,
                    'timeZone': 'America/Los_Angeles',
                }
            }

            event = service.events().insert(calendarId=id, body=event).execute() # add event to calendar

            # prompt user to ask if they want this event added to the database
            # create the popup
            popup = tk.Toplevel(main_frame)
            label = tk.Label(popup, text="Would you like this event added to stats?")
            label.grid(row=1, column=0,padx=20, pady=10)
            # add the button to the popup
            yes_button = tk.Button(popup, text="Yes", command=lambda: on_click("Yes", popup, connection, category, title.get(), start_json, end_json))
            no_button = tk.Button(popup, text="No", command=lambda: on_click("No", popup, connection, category, title.get(), start_json, end_json))
            yes_button.grid(row=0,column=1,padx=10, pady=5)
            no_button.grid(row=2,column=1,padx=10, pady=5)

            alert.grid_remove() # remove the "Timer has started" label
            title.delete(0, tk.END) # empty the input box
            title.grid(row=2, column=2, padx=10, pady=5, stick="e")
        else:
            messagebox.showerror("Error", f"You have not started tracking yet. You must click start.")

    def get_stats(category):
        """
        Get user's statistics and display them on the screen
        """
        _cleanup_checkboxes([], []) #only need the function here, not its return value

        global connection
        all_events = data.get_all_by_category(connection, category)

        # timedelta variables that will keep track of time worked in all 3 categories
        total_difference = datetime.timedelta()
        month_difference = datetime.timedelta()
        week_difference = datetime.timedelta()

        # getting today's date. will use this to check which categories the event fits into 
        now = datetime.datetime.now()

        for e in all_events:
            
            try:
                start_list = e[3].split("T")[0].split("-") + e[3].split("T")[1].split("-")[0].split(":")
                end_list = e[4].split("T")[0].split("-") + e[4].split("T")[1].split("-")[0].split(":")
                start_date = datetime.datetime(
                    int(start_list[0]), int(start_list[1]), int(start_list[2]), int(start_list[3]), int(start_list[4]))
                end_date = datetime.datetime(
                    int(end_list[0]), int(end_list[1]), int(end_list[2]), int(end_list[3]), int(end_list[4]))
                time_difference = end_date - start_date

                print(e[1], start_date, end_date, time_difference)

                total_difference += time_difference # adding to total time worked 

                # adding to monthly time worked
                if start_date.month == now.month:
                    month_difference += time_difference

                # adding to weekly time worked
                day_of_week = now.weekday()
                monday = now + datetime.timedelta(days= -day_of_week)
                if start_date >= monday:
                    week_difference += time_difference

            except IndexError as e:
                print(e)
        
        print(week_difference, month_difference, total_difference)

        # adjust the labels and display stats
        week_str = "Time spent working this week: %s" %(week_difference)
        month_str = "Time spent working this month: %s" %(month_difference)
        all_str = "Time spent working overall: %s" %(total_difference)

        # popup for stats
        stats_popup = tk.Toplevel(main_frame)
        week_label = tk.Label(stats_popup, text=week_str)
        month_label = tk.Label(stats_popup, text=month_str)
        all_label = tk.Label(stats_popup, text=all_str)
        done_stats = tk.Button(stats_popup, text="Done", command=lambda: stats_popup.destroy())
        week_label.grid(row=0, column=0, padx=5, pady=10)
        month_label.grid(row=1, column=0, padx=5, pady=10)
        all_label.grid(row=2, column=0, padx=5, pady=10)
        done_stats.grid(row=3, column=0, padx=5, pady=5)


    def display_events(service, id, category, cur, option):
        """
        This function grabs all events that happened in the last 4 weeks in the specified category and displays them
        """

        # dates for starting and ending of events
        now_unf = datetime.datetime.utcnow()
        diff = datetime.timedelta(weeks=-4)
        start_date_unf = now_unf + diff
        now = now_unf.isoformat() + "Z"
        start_date = start_date_unf.isoformat() + "Z"
        
        global row_ctr # declaring global variable to use
        global checkboxes

        events_result = service.events().list(calendarId=id, singleEvents=True, orderBy="startTime", timeMin=start_date, timeMax=now).execute()
        events = events_result.get("items", [])
        variables = []
        checkboxes = []
        events_parsing = []
        max_ctr = cur
        loop = 0

        for event in events:
            try:
                if loop >= max_ctr and max_ctr <= cur + 8:

                    start = event["start"].get("dateTime", event["start"].get("date"))
                    if len(start.split("T")) > 1:
                        start_str = start.split("T")[0] + " " + start.split("T")[1].split("-")[0]
                    else:
                        start_str = start.split("T")[0]

                    end = event["end"].get("dateTime", event["end"].get("date"))
                    if len(end.split("T")) > 1:
                        end_str = end.split("T")[0] + " " + end.split("T")[1].split("-")[0]
                    else:
                        end_str = end.split("T")[0]

                    name = event.get("summary", [])
                    if name == [] or name == '': # no title
                        name = "Untitled"
                    textstr = name + " | " + start_str + " - " + end_str
                    events_parsing.append([name, start, end])

                    row_ctr += 1

                    cur_var = tk.IntVar()
                    variables.append(cur_var)
                    cur_box = ttk.Checkbutton(main_frame, text=textstr, variable=cur_var)
                    cur_box.grid(row=row_ctr, column=1, padx = 5, pady = 5, stick="w")
                    checkboxes.append(cur_box)

                    max_ctr += 1

                loop += 1

            except KeyError:
                pass

        row_ctr += 1
        done_btn.configure(command=lambda: done_entry(variables, events_parsing, category, option))
        done_btn.grid(row=row_ctr, column=0, padx=10, pady=10, stick="w")
        see_more_btn.configure(command=lambda: see_more_helper(service, id, category, max_ctr, events, option, variables, events_parsing))
        see_more_btn.grid(row=row_ctr + 1, column=0, padx=10, pady=10, stick="w")

    def see_more_helper(service, id, category, max_ctr, events, option, variables, events_parsing):
        if max_ctr < len(events):
            global selected
            _cleanup_checkboxes(variables, events_parsing)
            print(selected)

            global row_ctr 
            row_ctr = row_ctr - 10

            display_events(service, id, category, max_ctr, option)
        else:
            messagebox.showerror("Error", f"No more events to see")

    def done_entry(variables, events_parsing, category, option):
        """
        We will add/delete the event to/from the database and get rid of events and done button
        """

        global selected
        _cleanup_checkboxes(variables, events_parsing)
        print(selected)

        global connection

        if option == "add":
            for s in selected:
                name = s[0]
                start_time = s[1]
                end_time = s[2]
                data.create_event(connection, category, name, start_time, end_time)

        if option == "del":
            for s in selected:
                name = s[0]
                start_time = s[1]
                end_time = s[2]
                data.delete_event(connection, category, name, start_time, end_time)
        
        selected = []
            

    def on_click(option, popup, connection, category, name, start_str, end_str):
        popup.destroy()

        if option == "Yes":
            data.create_event(connection, category, name, start_str, end_str)
        else:
            pass

    def _cleanup_checkboxes(variables, events_parsing):
        # in case the user had clicked on "add events" before this, but chose not to add anything, we will remove everything
        global checkboxes
        global selected

        counter = 0
        for v in variables:
            if v.get() == 1:
                selected.append(events_parsing[counter])
            counter += 1

        done_btn.grid_forget()
        see_more_btn.grid_forget()
        try: 
            for c in checkboxes:
                c.grid_forget()
        except Exception:
            pass


    # set up frames
    login_frame = ttk.Frame(root)
    login_frame.pack(expand=True)
    main_frame = ttk.Frame(root)

    # set up labels that we will add / remove later
    welcome_label = ttk.Label(main_frame, text="Google Calendar Productivity Extension")
    instruction = ttk.Label(main_frame, text="Pick a category to work in.")

    # setup buttons for login that we will now put on screen
    login_button = ttk.Button(root, text="Login To Start", command=login)
    login_button.pack()

    #setup for done and checkboxes so that we can remove them whenever
    done_btn = ttk.Button(main_frame, text="Done", command = None)
    see_more_btn = ttk.Button(main_frame, text="See More", command=None)

    root.mainloop()
    
if __name__ == "__main__":
    main()
