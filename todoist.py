from todoist_api_python.api import TodoistAPI
import requests
from classes import *
import datetime as dt
from datetime import timedelta
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os.path
import json
from collections import defaultdict
import pytz


class Scheduler:
    def __init__(self) -> None:
        self.today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # Below time is in PST
        # TODO: figure out why tzinfo=pytz.timezone("US/Pacific") wasn't working
        self.start = datetime(
            self.today.year,
            self.today.month,
            self.today.day,
            5,
            00,
            tzinfo=dt.timezone(dt.timedelta(days=-1, seconds=61200)),
        )
        self.end = datetime(
            self.today.year,
            self.today.month,
            self.today.day,
            23,
            00,
            tzinfo=dt.timezone(dt.timedelta(days=-1, seconds=61200)),
        )
        self.unspecified_tasks = []
        self.last_completed_task = None
        # timeline of events
        self.timeline = Timeline()
        self.todoist_tasks = set()
        self.authenticate()
        self.api = TodoistAPI("34fee45bdd071b7664156fea817dcd1094098a07")
        self.gcal_tasks = set()

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

    def get_gcal_tasks(self, is_beginning=False) -> None:
        """
        params:
        is_beginning is a boolean flag which is true iff we are populating from the start of the day (12am of the current day). It is false when user is running code in the middle of the day and is populating tasks from middle of the day.
        """
        try:
            service = build("calendar", "v3", credentials=self.creds)
            # calendar_list = service.calendarList().list().execute()
            # print(calendar_list)
            beginning_time = (
                datetime(self.today.year, self.today.month, self.today.day, 0, 0, 0)
                if is_beginning
                else datetime.now()
            )
            today_date = [
                beginning_time,
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

    def get_tasks(self) -> list:
        try:
            headers = {
                "Authorization": "Bearer 34fee45bdd071b7664156fea817dcd1094098a07",
                "Content-Type": "application/x-www-form-urlencoded",
            }

            data = 'sync_token=*&resource_types=["day_orders"]'

            response = requests.post(
                "https://api.todoist.com/sync/v9/sync", headers=headers, data=data
            )

            order = json.loads(response.text)["day_orders"]
            ordered_list = []

            for key, value in order.items():
                task = self.api.get_task(key)
                if task.is_completed == True or task.due.date != self.today.strftime(
                    "%Y-%m-%d"
                ):
                    continue
                name = task.content
                priority = value
                notes = ""
                time = task.description.split(":") if task.description else 0
                if time != 0:
                    hours = int(time[0])
                    min = int(time[1])
                else:
                    hours = 0
                    min = 15
                duration = hours * 60 + min
                new_task = EventTask(name, notes, duration, self.today, priority)

                ordered_list.append(new_task)

            ordered_list = sorted(ordered_list, key=lambda x: x.priority)
            return ordered_list

        except Exception as error:
            print(error)

    def timeblock_timeline(self, is_beginning=False) -> list:
        if is_beginning:
            cur_time = self.start
        else:
            cur_time = datetime.now(
                tz=dt.timezone(dt.timedelta(days=-1, seconds=61200))
            )

        blocks = []
        for task in self.timeline.timeline:
            if cur_time < task.start_time:
                time_diff = (task.start_time - cur_time).seconds / 60
                timebuffer = timedelta(minutes=15)
                task_start = cur_time + timebuffer
                while time_diff > 30:
                    next_block_end = task_start + timedelta(hours=1, minutes=30)
                    end_time = min(next_block_end, task.start_time - timebuffer)
                    timeblock = [task_start, end_time]
                    time_diff = (task.start_time - end_time).seconds / 60 - 30
                    task_start = end_time + timedelta(minutes=30)
                    blocks.append(timeblock)
            cur_time = task.end_time

        if cur_time < self.end:
            time_diff = (self.end - cur_time).seconds / 60
            timebuffer = timedelta(minutes=15)
            task_start = cur_time + timebuffer
            while time_diff > 30:
                next_block_end = task_start + timedelta(hours=1, minutes=30)
                end_time = min(next_block_end, self.end - timebuffer)
                timeblock = [task_start, end_time]
                time_diff = (self.end - end_time).seconds / 60 - 30
                task_start = end_time + timedelta(minutes=30)
                blocks.append(timeblock)

        return blocks

    def populate_timeline(self) -> None:
        """
        Adds the todoist tasks to the timeblocked sections of the timeline
        """
        ordered_tasks = self.get_tasks()

        timeblocks = self.timeblock_timeline()
        dict_timeline = defaultdict(list)
        for g_task in ordered_tasks:
            for idx, block in enumerate(timeblocks):
                time_in_block = (block[1] - block[0]).seconds / 60
                if g_task.duration <= time_in_block:
                    g_task.start_time = block[0]
                    g_task.end_time = g_task.start_time + timedelta(
                        minutes=g_task.duration
                    )
                    dict_timeline[idx].append(g_task)
                    block[0] = g_task.end_time
                    break

        final_timeline = []
        for idx in range(len(dict_timeline.keys())):
            final_timeline += dict_timeline[idx]
        self.timeline.timeline = final_timeline

    def remove_gcal_from_timeline(self) -> None:
        """
        remove gcal events from local timeline to prevent duplicate events being created
        """
        # TODO: how to create a list wrapper for timeline class?
        for event in self.gcal_tasks:
            for idx, timeline_event in enumerate(self.timeline.timeline):
                if event == timeline_event:
                    self.timeline.timeline.pop(idx)
                    break

    def update_calendar(self) -> None:
        scheduler.remove_scheduled_events()
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
            ]

            res = (
                service.events()
                .list(
                    calendarId="5afb0892b1bcaf333681a006b3367b2e3266d38e444d62a48e4b348fc64bf37a@group.calendar.google.com",
                    timeMin=dates[0].isoformat() + "-07:00",
                    singleEvents=True,
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

    # scheduler.timeblock_timeline()

    scheduler.populate_timeline()
    scheduler.update_calendar()

    # scheduler.remove_gcal_from_timeline()
    # date = datetime(2023, 4, 8, 5, 5, 5)
    # scheduler.remove_scheduled_events()
    # scheduler.remove_scheduled_events(date)
