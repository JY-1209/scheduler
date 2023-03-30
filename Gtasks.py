from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from classes import *
import os.path

from datetime import timedelta
from datetime import datetime


class Scheduler:
    def __init__(self) -> None:
        self.today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.start = self.cur_time = datetime(
            self.today.year, self.today.month, self.today.day, 6, 30
        )
        self.end = datetime(self.today.year, self.today.month, self.today.day, 11, 00)
        self.unspecified_tasks = []
        self.last_completed_task = None
        # timeline of events
        self.timeline = Timeline()
        self.authenticate()

    def authenticate(self):
        self.creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        scopes = [
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/tasks",
        ]
        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file("token.json", scopes)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", scopes
                )
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(self.creds.to_json())

    def get_gcal_tasks(self):
        try:
            service = build("calendar", "v3", credentials=self.creds)
            # calendar_list = service.calendarList().list().execute()
            # print(calendar_list)
            today_date = [
                datetime(self.today.year, self.today.month, self.today.day, 0, 0, 0),
                datetime(self.today.year, self.today.month, self.today.day, 23, 59, 59),
            ]
            events_result = (
                service.events()
                .list(
                    calendarId="5c02e21b477adaab0df81d57b444df9b8c977781461df83f0a0ab5957bfaf9b7@group.calendar.google.com",
                    timeMin=today_date[0].isoformat() + "-07:00",
                    timeMax=today_date[1].isoformat() + "-07:00",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            items = events_result["items"]

            for item in items:
                name = item["summary"]
                description = item["description"] if "description" in item else ""
                end = datetime.fromisoformat(item["end"]["dateTime"])
                start = datetime.fromisoformat(item["start"]["dateTime"])
                duration = (end - start).seconds / 60
                new_task = EventTask(
                    name, description, duration, self.today, 4, start, end
                )
                self.timeline.insert(new_task)
            print(self.timeline)
        except HttpError as error:
            print("An error occurred: %s" % error)

    def get_gtasks(self):
        try:
            service = build("tasks", "v1", credentials=self.creds)

            # results = service.tasklists().list().execute()
            # results = service.tasks().list().execute()
            results = service.tasks().list(tasklist="V3BCZU50NHVTNnpUMEV5Mw").execute()
            for item in results["items"]:
                print(item)
            # print(service.get())
        except HttpError as error:
            print("An error occurred: %s" % error)


if __name__ == "__main__":
    scheduler = Scheduler()
    scheduler.get_gcal_tasks()
    scheduler.get_gtasks()

