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
        print("BABABOOEY")
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        print("STEPPED IN DOOKIE")
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

    def login():
        try:
            creds = authenticate()

            login_button.pack_forget()
            login_frame.destroy()
            main_frame.pack()
            welcome_label.pack()

            service = build("calendar", "v3", credentials=creds)

            # Call the Calendar API
            now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
            print("Getting the upcoming 5 events")
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=5,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            print(events_result)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during authentication:\n{str(e)}")
            print(e)
            root.quit()

        # Use creds to access Google Calendar API
        # For example:
        # service = build('calendar', 'v3', credentials=creds)
        # ...s

    login_frame = tk.Frame(root)
    login_frame.pack()
    main_frame = tk.Frame(root)
    welcome_label = tk.Label(main_frame, text="Welcome to the Application!")

    login_button = tk.Button(root, text="Login with Google", command=login)
    login_button.pack()

    root.mainloop()

if __name__ == "__main__":
    main()
