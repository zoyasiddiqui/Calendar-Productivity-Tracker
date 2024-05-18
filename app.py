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
    root = ThemedTk(theme="breeze")
    #style = ttk.Style(root)
    #style.theme_use("clam")
    global start_time
    global end_time
    start_time = None
    end_time = None
    global connection
    connection = data.main()

    def login():
        try:
            creds = authenticate()

            # if authentication works, we move from the login page to the main page. 
            login_button.pack_forget()
            login_frame.destroy()
            main_frame.pack()
            welcome_label.grid(row=0, column=1, pady=10)
            instruction.grid(row=1, column=1, pady = 5)

            display(creds)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during authentication:\n{str(e)}")
            print(e)
            root.quit()
    
    def display(creds):
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
        row_ctr = 2
        for b in cal_btns:
            category = b.cget("text")
            b.config(command=lambda cat=category: act(cat, service, all_cals))
            b.grid(row=row_ctr, column=0, pady = 5,sticky="w")
            row_ctr += 1

    def act(category, service, all_cals):

        month_label.grid_remove()
        all_label.grid_remove()

        title = ttk.Entry(main_frame)
        title.insert(0, "Event Title")
        title.grid(row=2, column=2, padx=10, pady=5, sticky="e")
        alert = ttk.Label(main_frame, text="Timer has started") #will show up when they click start

        start = ttk.Button(main_frame, text="Start", command=lambda: get_start_time(alert))
        end = ttk.Button(main_frame, text="End", command=lambda: wrapup(service, all_cals[category], category, title, alert))
        start.grid(row=3, column=2, padx=5, pady=5, sticky="e")
        end.grid(row=4, column=2, padx=5, pady=5, sticky="e")
        stats = ttk.Button(main_frame, text="See stats for this category", command=lambda: get_stats(category))
        stats.grid(row=6, column=2, padx=5, pady=10, stick="e")

    def get_start_time(alert):
        global start_time
        start_time = datetime.datetime.now(datetime.timezone.utc)
        hours_added = datetime.timedelta(hours=-7)
        start_time += hours_added

        alert.grid(row=5, column=2, padx=5, pady=5, sticky="w") #tell users timer has started
    
    def wrapup(service, id, category, title, alert):
        global start_time
        global end_time
        global connection

        if start_time != None:
            end_time = datetime.datetime.now(datetime.timezone.utc)
            hours_added = datetime.timedelta(hours=-7)
            end_time += hours_added

            start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S-07:00")
            end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S-07:00")

            #adding the event to the user's google calendar with a json object
            event = {
                'summary': title.get(),
                'start': {
                    'dateTime': start_str,
                    'timeZone': 'America/Los_Angeles',
                },
                'end': {
                    'dateTime': end_str,
                    'timeZone': 'America/Los_Angeles',
                }
            }

            event = service.events().insert(calendarId=id, body=event).execute() # add event to calendar
            data.create_event(connection, category, start_str, end_str) # add event to database

            alert.grid_remove() # remove the "Timer has started" label
            title.delete(0, ttk.END) # empty the input box
            title.grid(row=2, column=2, padx=10, pady=5, sticky="e")
        else:
            messagebox.showerror("Error", f"You have not started tracking yet. You must click start.")

    def get_stats(category):
        global connection
        all_events = data.get_all_by_category(connection, category)
        t_hours = 0
        t_mins = 0
        t_secs = 0
        m_hours = 0
        m_mins = 0
        m_secs = 0

        # do all the work to find the amount of time worked
        for e in all_events:
            startdate = e[2].split("T")[1].split("-")[0].split(":")
            enddate = e[3].split("T")[1].split("-")[0].split(":")

            hour_delta = int(enddate[0]) - int(startdate[0])
            min_delta = int(enddate[1]) - int(startdate[1])
            secs_delta = int(enddate[2]) - int(startdate[2])
            if hour_delta > 0:
                t_hours += hour_delta
            if min_delta > 0:
                t_mins += min_delta
            if secs_delta > 0:
                t_secs += secs_delta
            
            event_month = int(e[2].split("T")[0].split("-")[1])
            now = datetime.datetime.now(datetime.timezone.utc)
            now_month = int(str(now).split()[0].split("-")[1])

            if event_month == now_month:
                if hour_delta > 0:
                    m_hours += hour_delta
                if min_delta > 0:
                    m_mins += min_delta
                if secs_delta > 0:
                    m_secs += secs_delta

        # adjust the labels and display stats
        month_str = "This month you worked for %d hours, %d minutes and %d seconds" % (m_hours,m_mins,m_secs)
        all_str = "Overall, you have worked for %d hours, %d minutes and %d seconds" %(t_hours,t_mins,t_secs)
        month_label.config(text=month_str)
        all_label.config(text=all_str)
        month_label.grid(row=7, column=2, pady=10, stick="e")
        all_label.grid(row=8, column=2, pady=5, stick="e")

    # set up frames
    login_frame = ttk.Frame(root)
    login_frame.pack()
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

    root.mainloop()
    
if __name__ == "__main__":
    main()
