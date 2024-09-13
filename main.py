import sys



import logging

# THIS WORKS!!!!
# POST https://wd3.myworkday.com/wday/authgwy/cineplex/login-auth.xml
# Headers:
# X-Workday-Client = 2024.36.21
# Content-Type = application/x-www-form-urlencoded
# userName = 
# password = 

# Mutlifactor authentication (2FA)
# GET https://wd3.myworkday.com/wday/authgwy/cineplex/api/authn/mfa/summary

# POST https://wd3.myworkday.com/wday/authgwy/cineplex/api/authn/mfa/challenge/workday/totp
# passcode = 629525

# https://www.w3.org/TR/webauthn-2

def main():
    driver = webdriver.Chrome()
    try:
        # Navigate to cineplex workday login page
        driver.get("https://wd3.myworkday.com/wday/authgwy/cineplex/login.htmld")
        

        pass
    finally:
        driver.quit()


# https://docs.python.org/3/library/__main__.html
if __name__ == "__main__":
    sys.exit(main())