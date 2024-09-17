from icalendar import Calendar, Event
import pytz
from datetime import datetime, tzinfo, date, time
from cineplex.shift import Shift
from uuid import uuid4

EVENT_NAME = "Cineplex Shift"

class Timetable:
    def __init__(self, tz: tzinfo) -> None:
        # Product Identifier https://www.kanzaki.com/docs/ical/prodid.html
        self.calendar = Calendar({
            "PRODID": "Algonquin timetable to .ics",
            "VERSION": "2.0"
        })
        self.tz = tz

    def add_shift(self, date: date, start_time: time, end_time: time):
        """Add a shift to the timetable"""

        # dtstart = shift.start.replace(tzinfo=self.tz)
        # dtend = shift.end.replace(tzinfo=self.tz)
        # dtstamp = datetime.now(tz=self.tz)

        # Create calendar date info
        dtstart = datetime.combine(date, start_time, tzinfo=self.tz)
        dtend = datetime.combine(date, end_time, tzinfo=self.tz)
        dtstamp = datetime.now(tz=self.tz)

        # Create iCalendar event
        event = Event({
            "SUMMARY": EVENT_NAME,
            "DTSTART": dtstart,
            "DTEND": dtend,
            "DTSTAMP": dtstamp,
            "UID": uuid4()
        })

        # Add event to calendar
        self.calendar.add_component(event)

    def to_ical(self):
        return self.calendar.to_ical()