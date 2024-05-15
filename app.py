import datetime
import os.path
import json
import tkinter as tk
from tkinter import messagebox
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# declare global variables
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate():
     # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
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
    root = tk.Tk()
    start_time = None
    end_time = None

    def login():
        try:
            creds = authenticate()

            login_button.pack_forget()
            login_frame.destroy()
            main_frame.pack()
            welcome_label.grid(row=0, column=0, pady=10)
            instruction.grid(row=1, column=0, pady = 5)

            display(creds)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during authentication:\n{str(e)}")
            print(e)
            root.quit()
    
    def display(creds):
        service = build("calendar", "v3", credentials=creds)
        page_token = None
        all_cals = {}
        cal_btns = []
        while True:
            calendar_list = service.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                cal = calendar_list_entry['summary']
                all_cals[cal] = calendar_list_entry['id']
                cal_btns.append(tk.Button(main_frame, text=cal, command=None))
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break
        
        row_ctr = 2
        for b in cal_btns:
            category = b.cget("text")
            b.config(command=lambda cat=category: act(cat, service, all_cals))
            b.grid(row=row_ctr, column=0, pady = 5,sticky="w")
            row_ctr += 1

    def act(category, service, all_cals):

        title = tk.Entry(main_frame)
        title.insert(0, "Event Title")
        title.grid(row=2, column=1, padx=10, pady=5, sticky="e")
        alert = tk.Label(main_frame, text="Timer has started")

        start = tk.Button(main_frame, text="Start", command=lambda: get_start_time(alert))
        end = tk.Button(main_frame, text="End", command=lambda: wrapup(service, all_cals[category], title.get(), alert))
        start.grid(row=3, column=1, padx=5, pady=5, sticky="e")
        end.grid(row=4, column=1, padx=5, pady=5, sticky="e")

    def get_start_time(alert):
        global start_time
        start_time = datetime.datetime.now(datetime.timezone.utc)
        hours_added = datetime.timedelta(hours=-7)
        start_time += hours_added

        alert.grid(row=5, column=1, padx=5, pady=5, sticky="w")
    
    def wrapup(service, id, title, alert):
        global start_time
        global end_time

        if start_time != None:
            end_time = datetime.datetime.now(datetime.timezone.utc)
            hours_added = datetime.timedelta(hours=-7)
            end_time += hours_added

            start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S-07:00")
            end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S-07:00")

            event = {
                'summary': title,
                'start': {
                    'dateTime': start_str,
                    'timeZone': 'America/Los_Angeles',
                },
                'end': {
                    'dateTime': end_str,
                    'timeZone': 'America/Los_Angeles',
                }
            }

            event = service.events().insert(calendarId=id, body=event).execute()

            alert.grid_remove()
            title.insert(0, "Event Title")
        else:
            messagebox.showerror("Error", f"You have not started tracking yet. You must click start.")
            root.quit()

    login_frame = tk.Frame(root)
    login_frame.pack()
    main_frame = tk.Frame(root)
    welcome_label = tk.Label(main_frame, text="Google Calendar Productivity Extension")
    instruction = tk.Label(main_frame, text="Pick a category to work in.")

    login_button = tk.Button(root, text="Login with Google", command=login)
    login_button.pack()

    root.mainloop()

if __name__ == "__main__":
    main()
