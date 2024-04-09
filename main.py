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

page_to_check = "https://ais.usvisa-info.com/en-ca/niv/schedule/#####/appointment"
assert "###" not in page_to_check, "Please fill in page_to_check with the url to the appointment rescheduling page"

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


def sign_in(driver):
    if "Sign in" not in driver.title:
        driver.get("https://ais.usvisa-info.com/en-ca/niv/users/sign_in")
        time.sleep(random.randint(1, 2))
    driver.execute_script("arguments[0].scrollIntoView();", driver.find_element(By.ID, "user_password"))
    driver.find_element(By.ID, "user_email").send_keys(account_email)
    driver.find_element(By.ID, "user_password").send_keys(account_password)
    time.sleep(random.randint(1, 2) / 3)
    checkbox = driver.find_element(By.CLASS_NAME, "radio-checkbox-group")
    driver.execute_script("arguments[0].scrollIntoView();", checkbox)
    time.sleep(random.randint(1, 2) / 3)
    checkbox.click()

    print("Looking for sign in button")
    b = driver.find_element(By.XPATH, "/html/body/div[5]/main/div[3]/div/div[1]/div/form/p[1]/input")
    print("Clicking sign in button: {}".format(b.text))
    time.sleep(random.randint(1, 2) / 3)
    driver.execute_script("arguments[0].scrollIntoView();", b)
    time.sleep(random.randint(1, 2) / 3)
    b.click()

    while True:
        time.sleep(1)
        if "Groups" in driver.title:
            break

    time.sleep(1)

    interview_info = driver.find_element(By.CLASS_NAME, "consular-appt")
    interview_info_text = interview_info.text
    print(interview_info_text)
    cur_date = re.search(r"[0-9]+ [a-zA-Z]+, 2024, [0-9]+:[0-9][0-9]", interview_info_text).group(0)
    cur_date = datetime.datetime.strptime(cur_date, "%d %B, %Y, %H:%M")

    notify("Next appointment: " + cur_date.strftime("%Y-%m-%d %H:%M"))

    time.sleep(random.randint(2, 5))
    return cur_date


def main():
    notify('visa scheduler started')

    # driver = webdriver.Firefox(service=webdriver.FirefoxService(executable_path='/snap/bin/geckodriver'))
    # driver = webdriver.Chrome()
    driver = webdriver.Edge()

    cur_date = sign_in(driver)
    try:
        while True:
            print("Checking page: " + page_to_check)
            driver.get(page_to_check)
            time.sleep(random.randint(30, 50) / 10.0)
            print("Loaded page: " + driver.title)

            if "Sign in" in driver.title:
                notify("User logged out")
                cur_date = sign_in(driver)
            elif "Schedule Appointments" in driver.title:
                try:
                    consulate = driver.find_element(By.ID, "appointments_consulate_appointment_facility_id").text

                    if "Vancouver" not in consulate:
                        notify("Consulate is not Vancouver: '{}'".format(consulate))
                        time.sleep(5)

                    no_appt_text = driver.find_element(By.ID, "consulate_date_time_not_available")
                    if no_appt_text.is_displayed():
                        print("No appointments available")
                    else:
                        date_field = driver.find_element(By.ID, "appointments_consulate_appointment_date")
                        driver.execute_script("arguments[0].scrollIntoView();", date_field)
                        time.sleep(random.randint(30, 50) / 10.0)
                        date_field.click()
                        time.sleep(random.randint(20, 30) / 10.0)

                        for d in driver.find_elements(By.CLASS_NAME, "undefined"):
                            if "ui-state-disabled" in d.get_attribute("class"):
                                continue
                            try:
                                year = int(d.get_attribute("data-year"))
                                month = int(d.get_attribute("data-month")) + 1
                                day = int(d.text)
                            except ValueError:
                                print("Unable to parse: " + d.text)
                                continue
                            date = datetime.datetime(year, month, day)
                            if date < cur_date:
                                notify("Found date: " + date.strftime("%Y-%m-%d"))
                                d.click()

                                while True:
                                    time.sleep(3)
                                    notify("Appointment found on " + date.strftime("%Y-%m-%d"))
                            else:
                                print("Skipping date: " + date.strftime("%Y-%m-%d"))
                except Exception as e:
                    notify("Error: " + str(e))
            else:
                notify("Unknown page: " + driver.title)

            wait_time = random.randint(45, 150)
            print("Waiting for {} seconds".format(wait_time))
            time.sleep(wait_time)
    except KeyboardInterrupt:
        driver.quit()
        notify('visa scheduler stopped')
        exit(0)


if __name__ == '__main__':
    main()

