import datetime
import os.path
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
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

  try:
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
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return

    # Prints the start and name of the next 10 events
    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      try:
        print(start, event["summary"])
      except KeyError:
        pass

    # Playing with Calendar Stuff
    # https://developers.google.com/calendar/api/v3/reference/calendarList#resource
    print("\nCalendar List Access Role Retrieval")
    calendar_list_entry = service.calendarList().get(calendarId='zoyasdq.04@gmail.com').execute()
    print(calendar_list_entry['accessRole'])

    # Getting all calendars for some user and listing them out
    print("\nPick a category.")
    page_token = None
    all_calendars = {}
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            all_calendars[calendar_list_entry['summary']] = calendar_list_entry['id']
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break
    
    print(all_calendars.keys())

    #prompting for entry info : category, start time, end time
    cur_cat = input("Which category would you like to work in? ")
    while(cur_cat not in all_calendars.keys()):
      print("This is not a valid option. Try again.")
      cur_cat = input("Which category would you like to work in? ")

    ready = input("Ready to start?")
    if (ready):
      start = datetime.datetime.now(datetime.timezone.utc)
    else:
      while(not ready):
         ready = input("Ready to start?")

    done = input("Are you done working?")
    if (done):
      end = datetime.datetime.now(datetime.timezone.utc)
    else:
      while(not done):
         done = input("Are you done working?")

    #adjusting time for time difference
    hours_added = datetime.timedelta(hours=-7)
    start_time = start + hours_added
    hours_added = datetime.timedelta(hours=-6) #need to add this so i don't have to wait between starting and ending
    end_time = end + hours_added

    start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S-07:00")
    end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S-07:00")

    title = input("Title your event: ")

    #Inserting event
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

    event = service.events().insert(calendarId=all_calendars[cur_cat], body=event).execute()
    print('Event created: %s' % (event.get('htmlLink')))

  except HttpError as error:
    print(f"An error occurred: {error}")

if __name__ == "__main__":
  main()
