from todoist_api_python.api_async import TodoistAPIAsync
from todoist_api_python.api import TodoistAPI

# Fetch tasks asynchronously
async def get_tasks_async():
    api = TodoistAPIAsync("df926ca1769ac235657957bf3372d7a8b12a0e20")
    try:
        tasks = await api.get_tasks()
        print(tasks)
    except Exception as error:
        print(error)

# Fetch tasks synchronously
def get_tasks_sync():
    api = TodoistAPI("df926ca1769ac235657957bf3372d7a8b12a0e20")
    try:
        tasks = api.get_tasks()
        print(tasks)
    except Exception as error:
        print(error)

get_tasks_sync()