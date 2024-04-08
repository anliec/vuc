from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
from sys import platform
import random
import re
import datetime

from pynotifier import NotificationClient, Notification
from pynotifier.backends import platform

c = NotificationClient()
c.register_backend(platform.Backend())

page_to_check = "https://ais.usvisa-info.com/en-ca/niv/schedule/56991018/appointment"


account_email = ""
account_password = ""
assert account_email != "" and account_password != "", "Please fill in account_email and account_password"

def notify(text, duration=5):
    print(text)
    c.notify_all(
        Notification(
            title=text,
            description="",
            duration=duration,
        )
    )


def main():
    notify('visa scheduler started')

    driver = webdriver.Firefox(service=webdriver.FirefoxService(executable_path='/snap/bin/geckodriver'))
    # driver = webdriver.Chrome()
    # driver = webdriver.Edge()

    driver.get("https://ais.usvisa-info.com/en-ca/niv/users/sign_in")

    time.sleep(random.randint(1, 2))

    driver.execute_script("arguments[0].scrollIntoView();", driver.find_element(By.ID, "user_password"))
    driver.find_element(By.ID, "user_email").send_keys(account_email)
    driver.find_element(By.ID, "user_password").send_keys(account_password)
    # time.sleep(random.randint(1, 2))
    # driver.execute_script("arguments[0].scrollIntoView();", driver.find_element(By.ID, "policy_confirmed"))
    # time.sleep(random.randint(1, 2) / 3)
    # driver.find_element(By.ID, "policy_confirmed").click()

    notify("Waiting for user to login")

    while True:
        time.sleep(1)
        if "Sign in" not in driver.title:
            break
    while True:
        time.sleep(1)
        if "Groups" in driver.title:
            break
    time.sleep(1)

    notify("User logged in")

    appt_info = driver.find_element(By.CLASS_NAME, "consular-appt")
    appt_info_text = appt_info.text
    print(appt_info_text)
    appt_date = re.search(r"[0-9]+ [a-zA-Z]+, 2024, [0-9]+:[0-9][0-9]", appt_info_text).group(0)
    appt_date = datetime.datetime.strptime(appt_date, "%d %B, %Y, %H:%M")

    notify("Next appointment: " + appt_date.strftime("%Y-%m-%d %H:%M"))

    time.sleep(random.randint(2, 5))

    try:
        while True:
            print("Checking page: " + page_to_check)
            driver.get(page_to_check)
            time.sleep(random.randint(3, 5))
            print("Loaded page: " + driver.title)

            consulate = driver.find_element(By.ID, "appointments_consulate_appointment_facility_id").text

            if "Vancouver" not in consulate:
                notify("Consulate is not Vancouver: '{}'".format(consulate))
                time.sleep(5)

            no_appt_text = driver.find_element(By.ID, "consulate_date_time_not_available")
            if not no_appt_text.is_displayed():
                while True:
                    notify("Appointment available!", duration=1)
                    time.sleep(1.5)

            # april_xpath = "/html/body/div[5]/div[1]/table/tbody"
            # may_xpath = "/html/body/div[5]/div[2]/table/tbody"
            # april_calandar_elem = driver.find_element(By.XPATH, april_xpath)
            # may_calandar_elem = driver.find_element(By.XPATH, may_xpath)

            time.sleep(random.randint(30, 120))
    except KeyboardInterrupt:
        driver.quit()
        notify('visa scheduler stopped')
        exit(0)


if __name__ == '__main__':
    main()

