class TimeDuration:
    def __init__(self, hours, minutes) -> None:
        self.hours = hours
        self.minutes = minutes


class EventTask:
    def __init__(self, name, description, duration, due_date, priority, start_time = None, end_time = None) -> None:
        """
        due_date: datetime object
        duration: duration of time to complete task (minutes)
        """
        self.name = name
        self.description = description
        self.duration = duration
        self.due_date = due_date
        self.priority = priority
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self) -> str:
        return f"event: {self.name}, description: {self.description}, duration: {self.duration}, due_date: {self.due_date}, priority: {self.priority}, start_time: {self.start_time}, end_time = {self.end_time}"


class Timeline:
    def __init__(self) -> None:
        self.timeline = []

    def insert(self, event_to_add) -> None:
        if not self.timeline:
            self.timeline.append(event_to_add)
            return

        # TODO: Consider scenario where the event_to_add end_time is past the start_time of the next event when inserted
        for idx, event in enumerate(self.timeline):
            if event_to_add.end_time < event.start_time:
                self.timeline.insert(idx, event_to_add)
                continue

        self.timeline.append(event_to_add)



    def __str__(self) -> str:
        timeline_string = ""
        for item in self.timeline:
            timeline_string += f"{str(item)} \n"
        return timeline_string
