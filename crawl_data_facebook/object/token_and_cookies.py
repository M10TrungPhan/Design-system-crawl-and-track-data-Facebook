import time
import re
import logging
import pickle

from bs4 import BeautifulSoup

from service.manage_account_facebook import ManageAccountFacebook
from utils.utils import setup_selenium_firefox
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


class TokenAndCookies:

    def __init__(self):
        self.user = None
        self.password = None
        self.account_facebook_db = ManageAccountFacebook()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cookies = None
        self.token_access = None
        self.flag_update_token = False

    def get_random_account_facebook(self):
        # account = self.account_facebook_db.select_random_account()
        # if account is None:
        #     return
        # self.user = account["user"]
        self.user = "tiki_lazada@protonmail.com"
        print(self.user)
        # self.password = account["password"]
        self.password = "A@123B@123"
        self.logger.info(f"USING ACCOUNT: {self.user}")

    def login_facebook_and_get_cookies(self):
        self.get_random_account_facebook()
        self.logger.info(f"GET COOKIES FROM FACEBOOK WITH ACCOUNT {self.user}")
        driver = setup_selenium_firefox()
        driver.get("https://www.facebook.com/")
        time.sleep(3)
        email_box = driver.find_element(By.ID, value="email")
        password_box = driver.find_element(By.ID, value="pass")
        email_box.send_keys(self.user)
        password_box.send_keys(self.password)
        password_box.send_keys(Keys.ENTER)
        time.sleep(5)
        cookies = driver.get_cookies()
        with open("cookies.pickle", "wb") as f:
            pickle.dump(cookies, f)
        driver.close()
        self.cookies = cookies
        return self.cookies

    def load_cookies(self):
        return self.cookies

    def get_token_access(self):
        self.logger.info(f"GET TOKEN ACCESS FROM FACEBOOK WITH ACCOUNT {self.user}")
        driver = setup_selenium_firefox()
        driver.get("https://www.facebook.com/")
        cookies_file = self.load_cookies()
        for cook in cookies_file:
            driver.add_cookie(cook)
        driver.get("view-source:https://business.facebook.com/content_management")
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "lxml")
        driver.close()
        string_ss = soup.text
        start, end = re.search(r"(\"accessToken\"\:\"\w+\")", string_ss).span()
        dict_access_token = string_ss[start:end]
        start_token, end_token = re.search(r"(\:\"\w+\")", dict_access_token).span()
        token = dict_access_token[start_token + 2: end_token - 1]
        self.token_access = token
        return self.token_access

    def load_token_access(self):
        return self.token_access

    def get_token_and_cookies(self):
        self.login_facebook_and_get_cookies()
        self.get_token_access()

    def update_new_token(self):
        if self.flag_update_token:
            return
        self.flag_update_token = True
        self.logger.info("UPDATE NEW ACCESS TOKEN")
        self.get_token_access()
        self.flag_update_token = False
        time.sleep(10)
