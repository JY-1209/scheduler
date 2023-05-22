from datetime import datetime

today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
print(today)
print(today.date())
print(today.isoformat())
print(str(today.date()))
