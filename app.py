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
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
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

    def login():
        """
        This function will move users from the login page to the main page
        """
        try:
            creds = authenticate()

            # if authentication works, we move frames 
            login_button.pack_forget()
            login_frame.destroy()
            main_frame.pack(expand=True)
            welcome_label.grid(row=0, column=1, pady=10)
            instruction.grid(row=1, column=1, pady = 5)

            display(creds)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during authentication:\n{str(e)}")
            print(e)
            root.quit()
    
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

    def act(category, service, all_cals):
        """
        This function opens up the side panel (with the event title, start, end buttons, etc) once the user
        clicks on a calendar
        """
        _cleanup_checkboxes()

        # remove the statistics labels from the last category we asked to view them from, if they are on the screen
        month_label.grid_remove()
        all_label.grid_remove()

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
        add = ttk.Button(main_frame, text="Add events for stats", command=lambda: display_events(service, all_cals[category], category, 0))
        add.grid(row=9, column=2, padx=5, pady=10, stick="e")

    def get_start_time(alert):
        """
        Record the time the user clicked "start", ie the start time of their task
        """
        _cleanup_checkboxes()

        # do actual function work
        global start_time
        start_time = datetime.datetime.now(datetime.timezone.utc)
        hours_added = datetime.timedelta(hours=-7)
        start_time += hours_added

        alert.grid(row=5, column=2, padx=5, pady=5, stick="w") #tell users timer has started
    
    def wrapup(service, id, category, title, alert):
        """
        Put together JSON object and make API call to add event to calendar. Add to database as well. 
        """
        _cleanup_checkboxes()
        
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

            start_str = start_json.split("T")[0] + " " + start_json.split("T")[1][0:5]
            end_str = end_json.split("T")[0] + " " + end_json.split("T")[1][0:5]

            event = service.events().insert(calendarId=id, body=event).execute() # add event to calendar

            # prompt user to ask if they want this event added to the database
            # create the popup
            popup = tk.Toplevel(main_frame)
            label = tk.Label(popup, text="Would you like this event added to stats?")
            label.grid(row=1, column=0,padx=20, pady=10)
            # add the button to the popup
            yes_button = tk.Button(popup, text="Yes", command=lambda: on_click("Yes", popup, connection, category, title.get(), start_str, end_str))
            no_button = tk.Button(popup, text="No", command=lambda: on_click("No", popup, connection, category, title.get(), start_str, end_str))
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
        _cleanup_checkboxes()

        global connection
        all_events = data.get_all_by_category(connection, category)
        
        hourdiff = 0
        mindiff = 0
        hourdifftotal = 0
        mindifftotal = 0

        # do all the work to find the amount of time worked
        for e in all_events:
            startdate = e[3].split()[0].split("-") + e[3].split()[1].split(":")
            enddate = e[4].split()[0].split("-") + e[4].split()[1].split(":")

            startday = int(startdate[2])
            endday = int(enddate[2]) 
            starthour = int(startdate[3]) 
            endhour = int(enddate[3]) 
            startmin = int(startdate[4])
            endmin = int(enddate[4])

            curhourdiff = 0
            curmindiff = 0

            if endday != startday:
                curhourdiff = (12-starthour) + endhour
            else:
                curhourdiff = endhour - starthour            

            if endhour != starthour and endmin < startmin:
                curhourdiff -= 1
                curmindiff = (60 - startmin) + endmin
            elif endhour != starthour and endmin > startmin:
                curmindiff = (60 - startmin) + endmin
            else:
                curmindiff = endmin - startmin

            hourdifftotal += curhourdiff
            mindifftotal += curmindiff

            # checking that we never have an invalid number of minute
            if mindifftotal > 60:
                hourdifftotal += 1
                mindifftotal -= 60

            now = datetime.datetime.now(datetime.timezone.utc)
            cur_month = int(str(now).split()[0].split("-")[1])
            event_month = int(startdate[1])
            if cur_month == event_month:
                hourdiff += curhourdiff
                mindiff += curmindiff

            # checking that we never have an invalid number of minute
            if mindiff > 60:
                hourdiff += 1
                mindiff -= 60         

        # adjust the labels and display stats
        month_str = "This month you worked for %d hours, %d minutes " % (hourdiff, mindiff)
        all_str = "Overall, you have worked for %d hours, %d minutes" %(hourdifftotal,mindifftotal)
        month_label.config(text=month_str)
        all_label.config(text=all_str)
        month_label.grid(row=7, column=2, pady=10, stick="e")
        all_label.grid(row=8, column=2, pady=5, stick="e")

    def display_events(service, id, category, cur):
        """
        This function grabs all events that happened in the last 3 months in the specified category and displays them
        """

        # dates for starting and ending of events
        now_unf = datetime.datetime.utcnow()
        diff = datetime.timedelta(weeks=-13)
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
                    if len(start.split("T")) == 2:
                        start_str = start.split("T")[0] + " " +start.split("T")[1][0:5]
                    else:
                        start_str = start.split("T")[0]
                    end = event["end"].get("dateTime", event["end"].get("date"))
                    if len(end.split("T")) == 2:
                        end_str = end.split("T")[0] + " " + end.split("T")[1][0:5]
                    else:
                        end_str = end.split("T")[0]
                    name = event.get("summary", [])
                    textstr = name + " " + start_str + " - " + end_str
                    events_parsing.append([name, start_str, end_str])

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

        #button they will click when done
        row_ctr += 1
        done_btn.configure(command=lambda: done_entry(variables, events_parsing, category))
        see_more_btn.configure(command=lambda: see_more_helper(service, id, category, max_ctr, events))
        done_btn.grid(row=row_ctr, column=0, padx=10, pady=10, stick="w")
        see_more_btn.grid(row=row_ctr + 1, column=0, padx=10, pady=10, stick="w")

    def see_more_helper(service, id, category, max_ctr, events):
        if max_ctr < len(events):
            _cleanup_checkboxes()

            global row_ctr 
            row_ctr = row_ctr - 10

            display_events(service, id, category, max_ctr)
        else:
            messagebox.showerror("Error", f"No more events to see")

    def done_entry(variables, events_parsing, category):
        """
        We will add the event to the database and get rid of events and done button
        """
        selected = {}
        counter = 0
        for v in variables:
            if v.get() == 1:
                selected[counter] = events_parsing[counter]
            counter += 1

        global connection
        for s in selected:
            name = selected[s][0]
            start_time = selected[s][1]
            end_time = selected[s][2]
            data.create_event(connection, category, name, start_time, end_time)

        _cleanup_checkboxes()

    def on_click(option, popup, connection, category, name, start_str, end_str):
        popup.destroy()

        if option == "Yes":
            data.create_event(connection, category, name, start_str, end_str)
        else:
            pass

    def _cleanup_checkboxes():
        # in case the user had clicked on "add events" before this, but chose not to add anything, we will remove everything
        global checkboxes

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
    
    month_label = ttk.Label(main_frame, text="")
    all_label = ttk.Label(main_frame, text="")
    month_label.grid(row=7, column=2, pady=10, stick="e")
    all_label.grid(row=8, column=2, pady=5, stick="e")

    # setup buttons for login that we will now put on screen
    login_button = ttk.Button(root, text="Login To Start", command=login)
    login_button.pack()

    #setup for done and checkboxes so that we can remove them whenever
    done_btn = ttk.Button(main_frame, text="Done", command = None)
    see_more_btn = ttk.Button(main_frame, text="See More", command=None)

    root.mainloop()
    
if __name__ == "__main__":
    main()
