from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pyotp

import os
from dotenv import load_dotenv

load_dotenv()

# 1. Login to workday with username, password and totp
# 2. Get and parse html of work schedule page
# Wednesday, 12am schedule updates


# TODO: Get to workbrain quicker and more reliably
# TODO: Parse calendar

driver = webdriver.Chrome()
driver.get("https://wd3.myworkday.com/wday/authgwy/cineplex/login.htmld")



try:
    # Click the "Login with Username and Password" button
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-automation-id='authSelectorOption']"))
    )[1].click()

    # Enter username
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-automation-id='userName'] input"))
    ).send_keys(os.environ["USER_NAME"])

    # Enter password
    driver.find_element(By.CSS_SELECTOR, "div[data-automation-id='password'] input").send_keys(os.environ["USER_PASSWORD"])

    # Click the "Sign in" button
    driver.find_element(By.CSS_SELECTOR, "button[data-automation-id='goButton']").click()

    # Enter TOTP code
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-automation-id='passcodeInputBox']"))
    ).send_keys(pyotp.TOTP(os.environ["TOTP_SECRET"]).now())

    # Click submit button
    driver.find_element(By.ID, "submitButton").click()

    # Click the "Remember this device" checkbox
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "tdCheckbox"))
    ).click()

    # Click the "Submit" button
    driver.find_element(By.ID, "submitButton").click()

    # No clue what this url emans
    driver.get("https://wd3.myworkday.com/cineplex/samlsso/autosubmit/6503$1.htmld")
    driver.get("https://workbrain.cineplex.com/etm/time/timesheet/etmTnsMonth.jsp?selectedTocID=181&parentID=10")

    input("Press Enter")

finally:
    driver.quit()

# div[data-automation-id='authSelectorOption'] (2nd one)
# input[data-automation-id='userName']
# input[data-automation-id='password']
# input[data-automation-id='goButton']