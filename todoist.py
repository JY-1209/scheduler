from todoist_api_python.api import TodoistAPI
from classes import *
from datetime import timedelta
from datetime import datetime


class Scheduler:
    def __init__(self) -> None:
        self.today = datetime.now()
        self.start = self.cur_time = datetime(
            self.today.year, self.today.month, self.today.day, 6, 30
        )
        self.end = datetime(self.today.year, self.today.month, self.today.day, 11, 00)
        # all_tasks will be an ordered list
        self.all_tasks = []
        self.unspecified_tasks = []

        self.last_completed_task = None
        self.timeline = Timeline()

    def normal_day(self):
        morning_schedule = EventTask(
            "Wake Up/Get Ready",
            "Wake Up, Drink Water, Brush Teeth, Breakfast",
            60,
            self.today,
            1,
        )
        morning_schedule.start_time = self.cur_time
        self.cur_time = self.cur_time + timedelta(minutes=morning_schedule.duration)
        morning_schedule.end_time = self.cur_time
        self.all_tasks.append(morning_schedule)

    def get_tasks(self):
        api = TodoistAPI("34fee45bdd071b7664156fea817dcd1094098a07")

        try:
            tasks = api.get_tasks()

            for task in tasks:
                print(task)
                new_task = EventTask(
                    task.content,
                    task.description,
                    task.labels[0] if task.labels else "",
                    task.due,
                    task.priority,
                )
                # no task label
                if not task.labels:
                    self.unspecified_tasks.append(new_task)
                else:
                    self.all_tasks.append(new_task)

            # print(unspecified_tasks)
            # print(all_tasks)
        except Exception as error:
            print(error)


if __name__ == "__main__":
    scheduler = Scheduler()
    scheduler.normal_day()
    scheduler.get_tasks()
