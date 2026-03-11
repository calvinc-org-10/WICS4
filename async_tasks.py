#HUEY BACKGROUND TASKS
from huey import SqliteHuey
huey = SqliteHuey(filename='huey.db')  # You can specify the filename for the SQLite database used by Huey

