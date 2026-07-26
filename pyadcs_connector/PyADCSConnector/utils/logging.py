import logging
from datetime import datetime

class MillisecondFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created)
        if datefmt:
            s = dt.strftime(datefmt)
            # Truncate microseconds to milliseconds
            return s[:-3]  # from 2025-07-28T19:09:47.123456 to 2025-07-28T19:09:47.123
        else:
            return dt.isoformat(timespec='milliseconds')
