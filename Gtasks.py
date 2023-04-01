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
        self.start = datetime(self.today.year, self.today.month, self.today.day, 6, 30)
        self.end = datetime(self.today.year, self.today.month, self.today.day, 11, 00)
        self.unspecified_tasks = []
        self.last_completed_task = None
        # timeline of events
        self.timeline = Timeline()
        self.gcal_tasks = set()
        self.authenticate()

    def authenticate(self) -> None:
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

    def get_gcal_tasks(self) -> None:
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
                self.timeline.gcal_insert(new_task)
                self.gcal_tasks.add(new_task)

        except HttpError as error:
            print("An error occurred: %s" % error)

    def get_gtasks(self) -> list:
        try:
            service = build("tasks", "v1", credentials=self.creds)
            # results = service.tasklists().list().execute()
            # results = service.tasks().list().execute()
            results = service.tasks().list(tasklist="V3BCZU50NHVTNnpUMEV5Mw").execute()

            ordered_list = []
            for item in results["items"]:
                name = item["title"]
                priority = item["position"]
                notes = item["notes"]
                time = notes.split(":")
                hours = int(time[0])
                min = int(time[1])
                duration = hours * 60 + min
                new_task = EventTask(name, "", duration, self.today, priority)
                ordered_list.append(new_task)
            ordered_list = sorted(ordered_list, key=lambda x: x.priority, reverse=False)
            # for item in ordered_list:
            #     print(item)

            return ordered_list
        except HttpError as error:
            print("An error occurred: %s" % error)

    def populate_timeline(self) -> None:
        ordered_tasks = self.get_gtasks()
        for g_task in ordered_tasks:
            # TODO: I cannot rely on the user or myself having a morning and night routine to signify the end of day. I need to modify the timeline such that it knows when the beginning and end of day are
            for idx, task in enumerate(self.timeline.timeline[:-1]):
                next_task = self.timeline.get(idx + 1)
                next_availability = (next_task.start_time - task.end_time).seconds / 60
                # exclude 15 minute time windows as they represent gaps between tasks
                if next_availability > 15 and g_task.duration < (
                    next_availability - 15
                ):
                    g_task.start_time = task.end_time + timedelta(minutes=15)
                    g_task.end_time = g_task.start_time + timedelta(
                        minutes=g_task.duration
                    )
                    self.timeline.gtask_insert(idx + 1, g_task)
                    break
                else:
                    continue

    def remove_gcal_from_timeline(self) -> None:
        """
        remove gcal events from local timeline to prevent duplicate events being created
        """
        # TODO: how to create a list wrapper?
        for event in self.gcal_tasks:
            for idx, timeline_event in enumerate(self.timeline.timeline):
                if event == timeline_event:
                    self.timeline.timeline.pop(idx)
                    break

    def update_calendar(self) -> None:
        try:
            service = build("calendar", "v3", credentials=self.creds)

            for item in self.timeline.timeline:
                event = {
                    "summary": item.name,
                    "description": item.description,
                    "start": {
                        "dateTime": item.start_time.isoformat(),
                        "timeZone": "America/Los_Angeles",
                    },
                    "end": {
                        "dateTime": item.end_time.isoformat(),
                        "timeZone": "America/Los_Angeles",
                    },
                }
                event = (
                    service.events()
                    .insert(
                        calendarId="5afb0892b1bcaf333681a006b3367b2e3266d38e444d62a48e4b348fc64bf37a@group.calendar.google.com",
                        body=event,
                    )
                    .execute()
                )

        except HttpError as error:
            print("An error occurred: %s" % error)

    def remove_scheduled_events(self, date=None):
        if not date:
            date = self.today

        try:
            service = build("calendar", "v3", credentials=self.creds)

            dates = [
                datetime(date.year, date.month, date.day, 0, 0, 0),
                datetime(date.year, date.month, date.day, 23, 59, 59),
            ]

            res = (
                service.events()
                .list(
                    calendarId="5afb0892b1bcaf333681a006b3367b2e3266d38e444d62a48e4b348fc64bf37a@group.calendar.google.com",
                    timeMin=dates[0].isoformat() + "-07:00",
                    timeMax=dates[1].isoformat() + "-07:00",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = res["items"]
            for event in events:
                service.events().delete(
                    calendarId="5afb0892b1bcaf333681a006b3367b2e3266d38e444d62a48e4b348fc64bf37a@group.calendar.google.com",
                    eventId=event["id"],
                ).execute()

        except HttpError as error:
            print("An error occurred: %s" % error)


if __name__ == "__main__":
    scheduler = Scheduler()
    scheduler.get_gcal_tasks()
    scheduler.populate_timeline()
    # print(scheduler.timeline)
    scheduler.remove_gcal_from_timeline()
    scheduler.update_calendar()
    # date = datetime(2023, 3, 31, 5, 5, 5)
    # scheduler.remove_scheduled_events(date)
