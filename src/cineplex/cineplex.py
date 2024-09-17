from requests import Session, Response
from datetime import datetime, date
from json import JSONDecodeError
from bs4 import BeautifulSoup
from pyotp import TOTP

# class Shift:
#     """A class that represents a shift at work"""
#     def __init__(self, start: datetime, end: datetime) -> None:
#         self.start = start
#         self.end = end
class Cineplex:
    """A class to interact with the Cineplex Workday/Workbrain API"""
    def __init__(self) -> None:
        self.session = Session()
        self.session.headers.update({"X-Workday-Client": "2024.37.11"}) # Required header for most requests

    @staticmethod
    def __parse_response(response: Response) -> dict | None:
        """Parse response from the Cineplex Workday API"""
        try:
            # JSON returned on success
            json = response.json()
            result = json["result"]
            if result != "SUCCESS":
                error_message = json["errorMessage"]
                raise RuntimeError(f"Workday request failed: {error_message}")
            return json
        except JSONDecodeError as error:
            # XML returned on failure
            soup = BeautifulSoup(response.text, "xml")
            failure = soup.find("wul:Failure")
            name = failure["Reason"]
            message = failure.get_text()
            raise RuntimeError("Workday request returned non-json response", name, message)

    def login(self, username: str, password: str, totp_secret: str) -> None:
        """Login to Cineplex Workday and Workbrain"""
        # Sometimes the InvalidCredentialsException will be returned until an actual web login is done. Why?

        response = self.session.post("https://wd3.myworkday.com/wday/authgwy/cineplex/login-auth.xml",
            data = {"userName": username, "password": password}
        )

        token = Cineplex.__parse_response(response)["sessionSecureToken"]

        response = self.session.post("https://wd3.myworkday.com/wday/authgwy/cineplex/api/authn/mfa/challenge/workday/totp",
            headers = {"Session-Secure-Token": token},
            json = {"passcode": TOTP(totp_secret).now()} # Could fail if request takes too long?
        )

        Cineplex.__parse_response(response)

        # SSO into Workbrain
        response = self.session.get("https://wd3.myworkday.com/cineplex/samlsso/autosubmit/6503$1.htmld")
        
        # Since Javascript is not supported, parse and submit the form
        soup = BeautifulSoup(response.text, "html.parser")
        inputs = {}
        for element in soup.find_all("input"):
            key = element["name"]
            value = element["value"]
            inputs.update({key: value})

        if len(inputs) < 1:
            raise RuntimeError("SSO Failed")

        response = self.session.post("https://workbrain.cineplex.com/samlsso", data=inputs)

    def get_shift(self, date: date):
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
        start_time = datetime.strptime(times[0].strip(), "%H:%M").time()
        end_time = datetime.strptime(times[1].strip(), "%H:%M").time()

        return (start_time, end_time)