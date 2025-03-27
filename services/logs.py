import datetime
from general.database import logs


class DBChangeCapture:
    @staticmethod
    async def log_change(event: str):

        log_entry = {"event": event, "timestamp": datetime.datetime.utcnow()}
        await logs.insert_one(log_entry)