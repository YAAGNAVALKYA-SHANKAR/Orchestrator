import datetime
from general.database import logs  # Ensure this is correctly imported


class DBChangeCapture:
    @staticmethod
    async def log_change(event: str, data: dict):
        """
        Logs a category-related change event.
        :param event: The type of event (e.g., 'Category Created', 'Category Updated')
        :param data: The data related to the event.
        """
        log_entry = {"event": event, "timestamp": datetime.datetime.utcnow(), **data}
        await logs.insert_one(log_entry)