from flask_sqlalchemy import SQLAlchemy
from huey import SqliteHuey
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

## MAIN DATABASE FILE
app_db = SQLAlchemy()


#HUEY BACKGROUND TASKS DATABASE
huey = SqliteHuey(filename='huey.db')  # You can specify the filename for the SQLite database used by Huey

#HUEY PROCESS STATUS DATABASE
huey_engine = create_engine(
    "sqlite:///huey_progress.db",
    connect_args={"check_same_thread": False}
)
HueySession = sessionmaker(bind=huey_engine)

def set_SQLite_WAL_mode():
# set the SQLite journal mode to WAL (Write-Ahead Logging) to allow for better concurrency between the main application and the background tasks when they are both accessing the same SQLite database. This is necessary because SQLite has limited support for concurrent writes, and using WAL mode can help mitigate some of those issues by allowing multiple readers and a single writer to access the database at the same time without blocking each other as much as in the default journal mode.
    with huey_engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
# set_SQLite_WAL_mode

        