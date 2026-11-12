"""Behave hooks: manage the Selenium driver lifecycle per scenario."""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

UI_URL = "http://localhost:4200"


def before_scenario(context, scenario):
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless=new")  # uncomment for headless runs
    context.driver = webdriver.Chrome(options=options)
    context.driver.set_page_load_timeout(30)


def after_scenario(context, scenario):
    driver = getattr(context, "driver", None)
    if driver is not None:
        driver.quit()
