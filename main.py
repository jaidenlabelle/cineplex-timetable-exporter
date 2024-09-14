import requests
import sys
import pyotp
from bs4 import BeautifulSoup
import logging

import os
from dotenv import load_dotenv

# https://www.w3.org/TR/webauthn-2

load_dotenv()

username = os.environ["CINEPLEX_USERNAME"]
password = os.environ["CINEPLEX_PASSWORD"]
totp_secret = os.environ["CINEPLEX_TOTP_SECRET"]

def main():
    session = requests.Session()
    session.headers.update({
        "X-Workday-Client": "2024.37.11"
    })

    # Returns JSON on success, XML on failure
    response = session.post(
        "https://wd3.myworkday.com/wday/authgwy/cineplex/login-auth.xml",
        headers = {"Content-Type": "application/x-www-form-urlencoded"},
        data = {"userName": username, "password": password}
    )

    json = response.json()
    token = json["sessionSecureToken"]

    # errorMessage: "You entered an incorrect code. Please try again."
    # status: "MFA_CHALLENGE"
    # result: "FAILURE"
    response = session.post(
        "https://wd3.myworkday.com/wday/authgwy/cineplex/api/authn/mfa/challenge/workday/totp",
        headers = {
            "Content-Type": "application/json",
            "Session-Secure-Token": token,
        },
        json = {"passcode": pyotp.TOTP(totp_secret).now()}
    )

    response = session.get("https://wd3.myworkday.com/cineplex/samlsso/autosubmit/6503$1.htmld")
    soup = BeautifulSoup(response.text, "html.parser")
    print(soup.prettify())

    # Since Javascript is not supported, parse and submit the form
    inputs = {}
    inputs.update({"RelayState": soup.find_all("input")[0]["value"]})
    inputs.update({"SAMLResponse": soup.find_all("input")[1]["value"]})
    print(inputs)

    response = session.post("https://workbrain.cineplex.com/samlsso", headers={"Content-Type": "application/x-www-form-urlencoded"}, data=inputs)
    response = session.get("https://workbrain.cineplex.com/etm/time/timesheet/etmTnsMonth.jsp?selectedTocID=181&parentID=10")
    print(response.text)

# https://docs.python.org/3/library/__main__.html
if __name__ == "__main__":
    sys.exit(main())