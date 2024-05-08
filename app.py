import tkinter as tk
from tkinter import messagebox
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# declare global variables
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate():
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    creds = flow.run_local_server(port=0)

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

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during authentication:\n{str(e)}")
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
