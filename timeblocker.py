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

PERSONAL_ID = "justinyg1209@gmail.com"
SCHEDULER_ID = "5afb0892b1bcaf333681a006b3367b2e3266d38e444d62a48e4b348fc64bf37a@group.calendar.google.com"


class Scheduler:
    def __init__(self) -> None:
        self.today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # Below time is in PST
        # TODO: figure out why tzinfo=pytz.timezone("US/Pacific") wasn't working
        # NOTE: Remember that the time and hours in 24hr format not AM/PM format
        self.start = datetime(
            self.today.year,
            self.today.month,
            self.today.day,
            7,
            00,
            tzinfo=dt.timezone(dt.timedelta(days=-1, seconds=61200)),
        )
        self.end = datetime(
            self.today.year,
            self.today.month,
            self.today.day + 1,
            0,
            0,
            tzinfo=dt.timezone(dt.timedelta(days=-1, seconds=61200)),
        )
        self.today_range = (
            datetime(self.today.year, self.today.month, self.today.day, 0, 0, 0),
            datetime(self.today.year, self.today.month, self.today.day, 23, 59, 59),
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
            beginning_time = self.today_range[0] if is_beginning else datetime.now()
            today_date = [beginning_time, self.today_range[1]]
            events_result = (
                service.events()
                .list(
                    calendarId=PERSONAL_ID,
                    timeMin=today_date[0].isoformat() + "-07:00",
                    timeMax=today_date[1].isoformat() + "-07:00",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            items = events_result["items"]

            for item in items:
                # The date key is in all day events and is not necessary for the scheduler. This if statement is to prevent the scheduler from adding all day events to the timeline.
                if "date" in item["start"]:
                    continue
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
            print("An error occurred in get_gcal_tasks(): %s" % error)

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
                # this try-except block is necessary for instances where a task is deleted but todoist still somehow stores a copy of this task which is then retrieved by the day_orders request. When the deleted task's ID is searched, it is unable to find the task.
                try:
                    task = self.api.get_task(key)
                except:
                    continue
                if task.is_completed == True or task.due.date != self.today.strftime(
                    "%Y-%m-%d"
                ):
                    continue
                name = task.content
                priority = value
                notes = ""
                time = task.description.split(":") if task.description else (0, 0)
                hours = int(time[0])
                min = int(time[1])
                duration = hours * 60 + min
                new_task = EventTask(name, notes, duration, self.today, priority)

                ordered_list.append(new_task)

            ordered_list = sorted(ordered_list, key=lambda x: x.priority)
            return ordered_list

        except Exception as error:
            print("get_tasks() failed")
            print(error)

    def timeblock_timeline(self, is_beginning=False) -> list:
        if is_beginning:
            cur_time = self.start
        else:
            cur_time = datetime.now(
                tz=dt.timezone(dt.timedelta(days=-1, seconds=61200))
            ) + dt.timedelta(minutes=2)

        blocks = []
        for task in self.timeline.timeline:
            # iff the start of the task from the google calendar is past the designated end time value, then break the loop
            if task.start_time > self.end:
                break
            if cur_time < task.start_time:
                time_diff = (task.start_time - cur_time).seconds / 60
                # timebuffer is the length of time b/t tasks
                timebuffer = timedelta(minutes=0)
                # breaktime is the length of time for a rest b/t timeblocks
                resttime = timedelta(minutes=0)
                # represents the length of WORK time in a timeblock. This variable + resttime represents the total length for a timeblock
                timeblock_time = timedelta(hours=2, minutes=0)
                task_start = cur_time + timebuffer
                while time_diff >= 15:  # while time_diff > 30:
                    next_block_end = task_start + timeblock_time
                    end_time = min(next_block_end, task.start_time - timebuffer)
                    timeblock = [task_start, end_time]
                    time_diff = (task.start_time - end_time).seconds / 60 - (
                        resttime.seconds / 60
                    )
                    task_start = end_time + resttime
                    blocks.append(timeblock)
            # only update the cur_time when the end_time is later b/c if there are multiple events that start at the same time, it's possible for the cur_time to not be sent to the event ending the latest
            cur_time = task.end_time if task.end_time > cur_time else cur_time

        # TODO: check if this is necessary
        if cur_time < self.end:
            time_diff = (self.end - cur_time).seconds / 60
            # timebuffer is the length of time b/t tasks
            timebuffer = timedelta(minutes=0)
            # breaktime is the length of time for a rest b/t timeblocks
            resttime = timedelta(minutes=0)
            # represents the length of WORK time in a timeblock. This variable + resttime represents the total length for a timeblock
            timeblock_time = timedelta(hours=2, minutes=0)
            task_start = cur_time + timebuffer
            while (
                time_diff >= 15
            ):  # 15 minutes is the minimum length of time for a task
                next_block_end = task_start + timeblock_time
                end_time = min(next_block_end, self.end - timebuffer)
                timeblock = [task_start, end_time]
                time_diff = (self.end - end_time).seconds / 60 - (resttime.seconds / 60)
                task_start = end_time + resttime
                blocks.append(timeblock)

        return blocks

    def populate_timeline(self) -> None:
        """
        Adds the todoist tasks to the timeblocked sections of the timeline
        """
        ordered_tasks = self.get_tasks()
        previously_ordered_tasks = self.get_scheduled_tasks(True)
        timeblocks = self.timeblock_timeline()
        dict_timeline = defaultdict(list)
        # TODO: Make sure that the names for todoist tasks aren't duplicated becasue the duplicate todoist tasks will be removed if the original name was previously slotted
        # TODO: add the 5 minute time buffer b/t tasks
        time_buffer = timedelta(minutes=5)
        for index, task in enumerate(ordered_tasks):
            # don't add the task if it was already scheduled
            if task.name in previously_ordered_tasks:
                continue
            # The task duration == 0 when the task is an all day event
            if task.duration == 0:
                task.start_time = task.due_date
                task.end_time = task.due_date + timedelta(days=1)
                dict_timeline["all_day"].append(task)
                continue
            first_short_timeblock = None
            # schedule the task in its corresponding timeblock
            for idx, block in enumerate(timeblocks):
                time_in_block = (block[1] - block[0]).seconds / 60
                if not first_short_timeblock and time_in_block >= 30:
                    first_short_timeblock = (idx, block)
                # Schedule the time if the task can fit in the timeblock
                if task.duration <= time_in_block:
                    task.start_time = block[0]
                    task.end_time = task.start_time + timedelta(minutes=task.duration)
                    dict_timeline[idx].append(task)
                    block[0] = task.end_time
                    # set first_short_timeblock to None so that the task isn't scheduled in a shorter timeblock
                    first_short_timeblock = None
                    break
            # If the task wasn't able to be scheduled in any of the timeblocks, try to find a shorter timeblock to fit it in
            # true iff the task was not scheduled
            if first_short_timeblock:
                idx = first_short_timeblock[0]
                block = first_short_timeblock[1]
                task.start_time = block[0]
                task.end_time = block[1]
                dict_timeline[idx].append(task)
                block[0] = task.end_time
                derivative_task = EventTask(
                    task.name,
                    task.description,
                    (task.end_time - task.start_time).seconds / 60,
                    task.due_date,
                    task.priority,
                )
                ordered_tasks.insert(index + 1, derivative_task)

        final_timeline = []
        for idx in range(len(dict_timeline.keys())):
            final_timeline += dict_timeline[idx]
        final_timeline += dict_timeline["all_day"]
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
        try:
            service = build("calendar", "v3", credentials=self.creds)

            for item in self.timeline.timeline:
                # the duration of the task is 0 when the task is an all day event
                if item.duration == 0:
                    event = {
                        "summary": item.name,
                        "description": item.description,
                        "start": {
                            "date": str(item.start_time.date()),
                        },
                        "end": {
                            "date": str(item.end_time.date()),
                        },
                    }
                else:
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
                        calendarId=SCHEDULER_ID,
                        body=event,
                    )
                    .execute()
                )

        except HttpError as error:
            print("An error occurred in update_calendar(): %s" % error)

    def remove_scheduled_events(self, date=None, is_beginning=False):
        date_time_range = (
            (
                datetime(date.year, date.month, date.day, 0, 0, 0),
                datetime(date.year, date.month, date.day, 23, 59, 59),
            )
            if date
            else self.today_range
        )

        try:
            service = build("calendar", "v3", credentials=self.creds)

            start = date_time_range[0] if is_beginning else datetime.now()

            res = (
                service.events()
                .list(
                    calendarId=SCHEDULER_ID,
                    timeMin=start.isoformat() + "-07:00",
                    timeMax=date_time_range[1].isoformat() + "-07:00",
                    singleEvents=True,
                )
                .execute()
            )

            events = res["items"]
            for event in events:
                service.events().delete(
                    calendarId=SCHEDULER_ID,
                    eventId=event["id"],
                ).execute()

        except HttpError as error:
            print("An error occurred in remove_scheduled_events(): %s" % error)

    def get_scheduled_tasks(self, is_earlier_today) -> set:
        """
        Get all scheduled tasks previously placed from the Scheduler Bot
        """
        try:
            service = build("calendar", "v3", credentials=self.creds)
            # calendar_list = service.calendarList().list().execute()
            # print(calendar_list)
            time_max = datetime.now() if is_earlier_today else self.today_range[1]
            events_result = (
                service.events()
                .list(
                    calendarId=SCHEDULER_ID,
                    timeMin=self.today_range[0].isoformat() + "-07:00",
                    timeMax=time_max.isoformat() + "-07:00",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            ids = set()
            for item in events_result["items"]:
                ids.add(item["summary"])

            return ids

        except HttpError as error:
            print("An error occurred in get_scheduled_tasks(): %s" % error)

    def run(self):
        self.remove_scheduled_events(is_beginning=True)
        print("=== PREVIOUSLY SCHEDULED EVENTS REMOVED ===")
        self.get_gcal_tasks()
        print("=== RETRIEVED TASKS FROM GOOGLE CALENDAR ===")
        self.populate_timeline()
        print("=== TIMELINE POPULATED ===")
        # for event in self.timeline.timeline:
        #     print(event)
        self.update_calendar()
        print("=== CALENDAR UPDATED ===")
        print("=== FINISHED ===")


if __name__ == "__main__":
    # TODO: glitch when repopulating timeline due to checking if previous tasks were already assigned. I think there shouldn't be a glitch b/c code should also be checking if the task was completed
    scheduler = Scheduler()
    # scheduler.get_gcal_tasks()
    # for i in scheduler.timeline.timeline:
    #     print(i)
    # scheduler.populate_timeline()
    # scheduler.get_scheduled_tasks(True)

    # date = datetime(2023, 4, 26, 5, 5, 5)
    # scheduler.remove_scheduled_events(date, is_beginning=True)
    # scheduler.remove_scheduled_events(is_beginning=True)
    scheduler.run()
