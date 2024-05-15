# Calendar-Productivity-Tracker
A productivity tracker that adds total time worked in some category to user's google calendar as an event

##Setting Up Credentials
To use this application, you'll need to set up your own credentials with Google Cloud Platform and configure the application to use them. Follow the steps below to create a Google Cloud project, enable the Google Calendar API, and generate OAuth client credentials.
###Create a Google Cloud Project
1. Go to the Google Cloud Console
2. Click on the project dropdown menu at the top of the page and select "New Project."
3. Enter a name for your project and click "Create."
###Enable the Google Calendar API
1. In the Google Cloud Console, navigate to the "APIs & Services" > "Library" page.
2. Search for "Google Calendar API" and click on it.
3. Click the "Enable" button to enable the API for your project.
###Generate OAuth Client Credentials
1. In the Google Cloud Console, navigate to the "APIs & Services" > "Credentials" page.
2. Click on the "Create credentials" dropdown and select "OAuth client ID."
3. Select "Desktop Application" as the application type.
4. Click "Create" to generate the OAuth client ID and client secret.
5. Download the JSON file containing your OAuth client credentials (credentials.json).
###Configure the Application
1. Clone this repository to your local machine.
2. Place the credentials.json file containing your OAuth client credentials in the root directory of the application.
3. Update the SCOPES variable in the application code to include the necessary scopes for your application, if necessary.
Run the application by executing python your_application.py and follow the on-screen instructions to authenticate with Google Calendar.

