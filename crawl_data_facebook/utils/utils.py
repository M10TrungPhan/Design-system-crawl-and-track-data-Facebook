import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from config.config import Config


def setup_selenium_firefox():
    ser = Service(r"driverbrower\geckodriver.exe")
    firefox_options = FirefoxOptions()
    firefox_options.set_preference("media.volume_scale", "0.0")
    firefox_options.set_preference('devtools.jsonview.enabled', False)
    firefox_options.set_preference('dom.webnotifications.enabled', False)
    firefox_options.add_argument("--test-type")
    firefox_options.add_argument('--ignore-certificate-errors')
    firefox_options.add_argument('--disable-extensions')
    firefox_options.add_argument('disable-infobars')
    firefox_options.add_argument("--incognito")
    firefox_options.add_argument("--headless")
    driver = webdriver.Firefox(service=ser, options=firefox_options)
    return driver


def setup_logging():
    config = Config()
    os.makedirs(config.logging_folder, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | [%(levelname)s] | %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(config.logging_folder, "crawl_data.log"), encoding="utf8"),
            logging.StreamHandler()
        ]
    )

setup_logging()

