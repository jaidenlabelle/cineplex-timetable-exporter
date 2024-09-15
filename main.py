import requests
import sys
import pyotp
from bs4 import BeautifulSoup
import logging
import datetime
import pytz
import icalendar
import uuid
from json import JSONDecodeError

import os
from dotenv import load_dotenv

# https://www.w3.org/TR/webauthn-2

tz = pytz.timezone("America/Toronto")
calendar = icalendar.Calendar()

# Product Identifier https://www.kanzaki.com/docs/ical/prodid.html
calendar.add("PRODID", "Cineplex timetable to .ics")
calendar.add("VERSION", "2.0") # iCalendar spec version

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
calendar.add_component(timezone)

# Get secrets
load_dotenv()
username = os.environ["CINEPLEX_USERNAME"]
password = os.environ["CINEPLEX_PASSWORD"]
totp_secret = os.environ["CINEPLEX_TOTP_SECRET"]

def getShift(session: requests.Session, date: datetime.date):
    '''Get details about shift for a given date, user must be logged in'''

    # Convert date to mm.dd.yyyy
    date_str = date.strftime("%m.%d.%Y")

    # Form request url
    url = f"https://workbrain.cineplex.com/etm/time/timesheet/etmTnsDay.jsp?date={date_str}"

    # Send GET request
    response = session.get(url)

    # Parse start and end time
    soup = BeautifulSoup(response.text, "html.parser")

    # Get date container
    td = soup.find("td", class_ = "currentDay")
    # Get date shift times as strings hh:mm - hh:mm
    try:
        times = td.find("div", class_ = "calendarTextShiftTime").getText().split("-")
    except AttributeError:
        print("No shift")
        return

    # Get shift start and end time
    start_time = datetime.datetime.strptime(times[0].strip(), "%H:%M").time()
    end_time = datetime.datetime.strptime(times[1].strip(), "%H:%M").time()

    # Create calendar date info
    dtstart = datetime.datetime.combine(date, start_time, tzinfo=tz)
    dtend = datetime.datetime.combine(date, end_time, tzinfo=tz)
    dtstamp = datetime.datetime.now(tz=tz)

    # Create iCalendar event
    event = icalendar.Event()
    event.add('SUMMARY', "Cineplex Shift")
    event.add('DTSTART', dtstart)
    event.add('DTEND', dtend)
    event.add('DTSTAMP', dtstamp)
    event.add('UID', uuid.uuid4())

    calendar.add_component(event)

def login(session: requests.Session, username: str, password: str, totp_secret: str):
    """Login to Workday and Workbrain"""

    # Returns JSON on success, XML on failure
    response = session.post("https://wd3.myworkday.com/wday/authgwy/cineplex/login-auth.xml",
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
    response = session.post("https://wd3.myworkday.com/wday/authgwy/cineplex/api/authn/mfa/challenge/workday/totp",
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
    response = session.get("https://wd3.myworkday.com/cineplex/samlsso/autosubmit/6503$1.htmld")
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
    response = session.post("https://workbrain.cineplex.com/samlsso", data=inputs)

    



def main():
    session = requests.Session()
    session.headers.update({
        "X-Workday-Client": "2024.37.11"
    })

    # Login to Workday and Workbrain
    login(session, username, password, totp_secret)

    for i in range(0, 7):
        getShift(session, datetime.datetime.now(tz=tz).date() + datetime.timedelta(days=i))

    with open("output.ics", "wb") as file:
        file.write(calendar.to_ical())
        print("Calendar written")

# https://docs.python.org/3/library/__main__.html
if __name__ == "__main__":
    sys.exit(main())