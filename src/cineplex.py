import requests
import pyotp
from bs4 import BeautifulSoup
from json import JSONDecodeError
import datetime

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
            soup = BeautifulSoup(response.text, "xml")
            reason = soup.find("wul:Failure")["Reason"]
            message = soup.find("wul:Failure").get_text()
            raise RuntimeError("Workday login returned non-json response", reason, message)

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
            raise RuntimeError("SSO Failed")

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
    