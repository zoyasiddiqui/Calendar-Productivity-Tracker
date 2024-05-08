import tkinter as tk
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate():
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    creds = flow.run_local_server(port=0)

    return creds

def main():
    root = tk.Tk()

    def login():
        creds = authenticate()
        # Use creds to access Google Calendar API
        # For example:
        # service = build('calendar', 'v3', credentials=creds)
        # ...

    login_button = tk.Button(root, text="Login with Google", command=login)
    login_button.pack()

    root.mainloop()

if __name__ == "__main__":
    main()
