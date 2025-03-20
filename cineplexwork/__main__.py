"""Command line interface"""
import argparse
from dotenv import load_dotenv
from pytz import timezone, all_timezones
import os
from cineplexwork.cineplex import Cineplex
from cineplexwork.schedule import Schedule
from datetime import datetime, timedelta

parser = argparse.ArgumentParser(
    description='Get employee schedule from Cineplex Workbrain',
    epilog='Created by Jaiden Labelle'
)

parser.add_argument('filename', type=str, help='Name of the file to save the schedule to')
parser.add_argument('timezone', type=str, help='Timezone of the schedule (e.g. America/Toronto)', choices=all_timezones, metavar="timezone")
args = parser.parse_args()

tz = timezone(args.timezone)

load_dotenv()
username = os.environ["CINEPLEX_USERNAME"]
password = os.environ["CINEPLEX_PASSWORD"]
totp_secret = os.environ["CINEPLEX_TOTP_SECRET"]

print(f"Getting schedule for {username} in timezone {tz}")

cineplex = Cineplex()
calendar = Schedule(tz)

# Load existing calendar
calendar.load(args.filename)

# Login to Workday and Workbrain
cineplex.login(username, password, totp_secret)

# Check today and the next 7 days for shifts
for i in range(0, 7):
    date = datetime.now(tz=tz).date() + timedelta(days=i)
    shift = cineplex.get_shift(date)
    if shift:
        print(f"Shift on {date}, {shift.start} - {shift.end}")
        calendar.add_shift(date, shift.start.time(), shift.end.time())
    else:
        print(f"No shift on {date}")

# Output .ics file
with open(args.filename, "wb") as file:
    file.write(calendar.to_ical())
    print("Calendar written")