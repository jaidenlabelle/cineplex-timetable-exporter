from cineplex import Cineplex
from shift_calendar import ShiftCalendar
import pytz
import os
import datetime
from dotenv import load_dotenv

# Get secrets
load_dotenv()
username = os.environ["CINEPLEX_USERNAME"]
password = os.environ["CINEPLEX_PASSWORD"]
totp_secret = os.environ["CINEPLEX_TOTP_SECRET"]

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