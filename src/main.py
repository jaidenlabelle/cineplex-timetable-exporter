# Packages to interact with cineplex api
import requests
import pyotp
from bs4 import BeautifulSoup
from json import JSONDecodeError
import datetime
import icalendar
import pytz
import uuid

import os
from dotenv import load_dotenv

# Get secrets
load_dotenv()
username = os.environ["CINEPLEX_USERNAME"]
password = os.environ["CINEPLEX_PASSWORD"]
totp_secret = os.environ["CINEPLEX_TOTP_SECRET"]

class Cineplex:
    """A class to interact with the Cineplex Workday/Workbrain API"""
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"X-Workday-Client": "2024.37.11"}) # Required header for most requests

    def login(self, username: str, password: str, totp_secret: str) -> None:
        """Login to Cineplex Workday and Workbrain"""

        # https://www.w3.org/TR/webauthn-2
        
         # Returns JSON on success, XML on failure
        response = self.session.post("https://wd3.myworkday.com/wday/authgwy/cineplex/login-auth.xml",
            data = {"userName": username, "password": password}
        )
        
        try:
            json = response.json()
            result = json["result"]
            # TODO: Respond to errors
            if result != "SUCCESS":
                err_message = json["errorMessage"]
                raise RuntimeError(f"Workday login failed: {err_message}")
            token = json["sessionSecureToken"]
        except JSONDecodeError as err:
            raise RuntimeError("Workday login returned non-json response", err)

        totp = pyotp.TOTP(totp_secret)

        # errorMessage: "You entered an incorrect code. Please try again."
        # status: "MFA_CHALLENGE"
        # result: "FAILURE"

        # Error that happens when running too often
        # errorMessage: "Your session has expired, please re-enter your password"
        response = self.session.post("https://wd3.myworkday.com/wday/authgwy/cineplex/api/authn/mfa/challenge/workday/totp",
            headers = {"Session-Secure-Token": token},
            json = {"passcode": totp.now()} # Could fail if request takes too long?
        )

        try:
            json = response.json()
            result = json["result"]
            # TODO: Respond to errors
            if result != "SUCCESS":
                err_message = json["errorMessage"]
                raise RuntimeError(f"Workday MFA failed: {err_message}")
        except JSONDecodeError as err:
            raise RuntimeError("Workday MFA TOTP returned non-json response", err)

        # SSO into Workbrain
        response = self.session.get("https://wd3.myworkday.com/cineplex/samlsso/autosubmit/6503$1.htmld")
        soup = BeautifulSoup(response.text, "html.parser")

        # Since Javascript is not supported, parse and submit the form
        inputs = {}
        for element in soup.find_all("input"):
            key = element["name"]
            value = element["value"]
            inputs.update({key: value})

        if len(inputs) < 1:
            raise RuntimeError("SSO Failed, this happens often, retry a few times")

        # TODO: Handle any errors from this request
        response = self.session.post("https://workbrain.cineplex.com/samlsso", data=inputs)

    def get_shift(self, date: datetime.date) -> tuple[datetime.time] | None:
        """Get shift start and end times for a given date"""

        # Convert date to mm.dd.yyyy
        date_str = date.strftime("%m.%d.%Y")

        # Form request url
        url = f"https://workbrain.cineplex.com/etm/time/timesheet/etmTnsDay.jsp?date={date_str}"

        # Send GET request
        response = self.session.get(url)

        # Parse start and end time
        soup = BeautifulSoup(response.text, "html.parser")

        # Get date container
        td = soup.find("td", class_ = "currentDay")
        # Get date shift times as strings hh:mm - hh:mm
        try:
            times = td.find("div", class_ = "calendarTextShiftTime").getText().split("-")
        except AttributeError:
            # There is no shift
            return None
        
        # Get shift start and end time
        start_time = datetime.datetime.strptime(times[0].strip(), "%H:%M").time()
        end_time = datetime.datetime.strptime(times[1].strip(), "%H:%M").time()

        return (start_time, end_time)
    
class ShiftCalendar:
    def __init__(self, tz) -> None:
        self.calendar = icalendar.Calendar()
        self.tz = tz

        # Product Identifier https://www.kanzaki.com/docs/ical/prodid.html
        self.calendar.add("PRODID", "Algonquin timetable to .ics")
        self.calendar.add("VERSION", "2.0") # iCalendar spec version

        # TODO: Document this better
        # Create timezone for America/Toronto
        timezone = icalendar.Timezone()
        timezone.add('TZID', 'America/Toronto')
        
        # TODO: Use pytz timezone to get this information?
        # EDT timezone info
        daylight_timezone = icalendar.TimezoneDaylight()
        daylight_timezone.add('TZOFFSETFROM', datetime.timedelta(hours=-5))
        daylight_timezone.add('TZOFFSETTO', datetime.timedelta(hours=-4))
        daylight_timezone.add('TZNAME', 'EDT')
        daylight_timezone.add('DTSTART', datetime.datetime(1970, 3, 8))
        daylight_timezone.add('RRULE', {'FREQ': 'YEARLY', 'BYMONTH': 3, 'BYDAY': '2SU'})

        # EST timezone info
        standard_timezone = icalendar.TimezoneStandard()
        standard_timezone.add('TZOFFSETFROM', datetime.timedelta(hours=-4))
        standard_timezone.add('TZOFFSETTO', datetime.timedelta(hours=-5))
        standard_timezone.add('TZNAME', 'EST')
        standard_timezone.add('DTSTART', datetime.datetime(1970, 11, 1))
        standard_timezone.add('RRULE', {'FREQ': 'YEARLY', 'BYMONTH': 11, 'BYDAY': '1SU'})

        # Combine
        timezone.add_component(daylight_timezone)
        timezone.add_component(standard_timezone)
        self.calendar.add_component(timezone)

    def add_shift(self, date: datetime.date, start_time: datetime.time, end_time: datetime.time):
        """Add shift to calendar"""
        
        # Create calendar date info
        dtstart = datetime.datetime.combine(date, start_time, tzinfo=self.tz)
        dtend = datetime.datetime.combine(date, end_time, tzinfo=self.tz)
        dtstamp = datetime.datetime.now(tz=self.tz)

        # Create iCalendar event
        event = icalendar.Event()
        event.add('SUMMARY', "Cineplex Shift")
        event.add('DTSTART', dtstart)
        event.add('DTEND', dtend)
        event.add('DTSTAMP', dtstamp)
        event.add('UID', uuid.uuid4())

        # Add event to calendar
        self.calendar.add_component(event)

    def to_ical(self):
        return self.calendar.to_ical()

def main():
    tz = pytz.timezone("America/Toronto") # TODO: Not hardcode this
    cineplex = Cineplex()
    calendar = ShiftCalendar(tz)

    # Login to Workday and Workbrain
    cineplex.login(username, password, totp_secret)

    # Check today and the next 7 days for shifts
    for i in range(0, 7):
        date = datetime.datetime.now(tz=tz).date() + datetime.timedelta(days=i)
        times = cineplex.get_shift(date)
        if times:
            (start_time, end_time) = times
            print(f"Shift on {date}, {start_time} - {end_time}")
            calendar.add_shift(date, start_time, end_time)
        else:
            print(f"No shift on {date}")

    # Output .ics file
    with open("output.ics", "wb") as file:
        file.write(calendar.to_ical())
        print("Calendar written")

if __name__ == "__main__":
    main()