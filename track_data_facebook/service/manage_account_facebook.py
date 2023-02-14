from config.config import Config
from object.singleton import Singleton
from object.account_fb_request import AccountFacebookRequest
from database.facebook_db import AccountFacebookCollection
import hashlib
import logging
import concurrent.futures

from utils.utils import setup_selenium_firefox
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import re
from threading import Thread


class ManageAccountFacebook(Thread, metaclass=Singleton):

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.account_fb_collection = AccountFacebookCollection()
        self.logger = logging.getLogger(self.__class__.__name__)

    def add_account_facebook(self, account: AccountFacebookRequest):
        id_user = hashlib.md5(account.username.encode("utf-8")).hexdigest()
        if self.account_fb_collection.query_account_follow_id(id_user) is not None:
            return "ACCOUNT EXISTED"
        username = account.username
        password = account.password
        data = {"_id": id_user, "user": username, "password": password, "status": account.status,
                "token_access": account.token_access, "cookies": account.cookies}
        self.account_fb_collection.create_account(data)
        return "ACCOUNT HAVE CREATED SUCCESSFULLY"

    def remove_account_facebook(self, account: AccountFacebookRequest):
        id_user = hashlib.md5(account.username.encode("utf-8")).hexdigest()
        self.account_fb_collection.remove_account({"_id": id_user})
        return "ACCOUNT HAVE REMOVED SUCCESSFULLY"

    def select_random_account(self):
        account = self.account_fb_collection.random_account()
        if account is None:
            return None
        return account

    def update_information_account_api(self, account: AccountFacebookRequest):
        return self.account_fb_collection.update_information_account_api(account)

    def check_information_account(self, account: AccountFacebookRequest):
        id_user = hashlib.md5(account.username.encode("utf-8")).hexdigest()
        account_query = self.account_fb_collection.query_account_follow_id(id_user)
        if account_query is None:
            return "ACCOUNT IS NOT EXISTED"
        return account_query

    def get_information_all_account(self):
        return self.account_fb_collection.get_information_all_account()

    def login_facebook_and_get_cookies(self, user, password):
        self.logger.info(f"GET COOKIES FROM FACEBOOK WITH ACCOUNT {user}")
        driver = setup_selenium_firefox()
        driver.get("https://www.facebook.com/")
        time.sleep(3)
        email_box = driver.find_element(By.ID, value="email")
        password_box = driver.find_element(By.ID, value="pass")
        email_box.send_keys(user)
        password_box.send_keys(password)
        password_box.send_keys(Keys.ENTER)
        time.sleep(5)
        driver.get("https://www.facebook.com/me?")
        time.sleep(3)
        try:
            user_name = driver.find_element(By.CLASS_NAME, value="x1heor9g x1qlqyl8 x1pd3egz x1a2a7pz".
                                            replace(" ", ".")).text
        except:
            user_name = None
        cookies = driver.get_cookies()
        driver.close()
        return cookies, user_name

    def get_token_access(self, user, cookies):
        self.logger.info(f"GET TOKEN ACCESS FROM FACEBOOK WITH ACCOUNT {user}")
        driver = setup_selenium_firefox()
        driver.get("https://www.facebook.com/")
        cookies_file = cookies
        for cook in cookies_file:
            driver.add_cookie(cook)
        driver.get("view-source:https://business.facebook.com/content_management")
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "lxml")
        driver.close()
        string_ss = soup.text
        if re.search(r"(\"accessToken\"\:\"\w+\")", string_ss) is None:
            return None
        start, end = re.search(r"(\"accessToken\"\:\"\w+\")", string_ss).span()
        dict_access_token = string_ss[start:end]
        start_token, end_token = re.search(r"(\:\"\w+\")", dict_access_token).span()
        token = dict_access_token[start_token + 2: end_token - 1]
        return token

    def update_token(self, user, token):
        account = AccountFacebookRequest(user)
        account.token_access = token
        self.account_fb_collection.update_information_account_api(account)

    def update_cookies(self, user, cookies):
        account = AccountFacebookRequest(user)
        account.token_access = cookies
        self.account_fb_collection.update_information_account_api(account)

    def update_status(self, user, status):
        account = AccountFacebookRequest(user)
        account.status = status
        self.account_fb_collection.update_information_account_api(account)

    def update_information_for_account(self, user, password):
        cookies, account_name = self.login_facebook_and_get_cookies(user, password)
        token_access = self.get_token_access(user, cookies)
        account = AccountFacebookRequest(user)
        if token_access is None:
            account.status = "account block"
        else:
            account.status = "active"
        # if self.check_block_type_function_load_comment():
        #     account.status = "temporary block"
        # else:
        #     account.status = "active"
        account.token_access = token_access
        account.cookies = cookies
        account.account_name = account_name
        self.account_fb_collection.update_information_account_api(account)

    def update_information_for_all_account(self):
        self.logger.info("UPDATE INFORMATION FOR ALL ACCOUNT")
        list_account = self.account_fb_collection.get_information_all_account()
        # for account in list_account:
        #     self.update_information_for_account(account["user"], account["password"])
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(list_account)) as executor:
            [executor.submit(self.update_information_for_account, account["user"],
                             account["password"]) for account in list_account]

    def update_information_for_all_account_to_comment(self):
        self.logger.info("UPDATE INFORMATION FOR ALL ACCOUNT COMMENT")
        list_account = self.account_fb_collection.get_information_all_account()
        list_account_new = []
        for account in list_account:
            if account["status"] == "comment":
                list_account_new.append(account)
        print()
        for account in list_account_new:
            self.update_information_for_account(account["user"], account["password"])
        # with concurrent.futures.ThreadPoolExecutor(max_workers=len(list_account)) as executor:
        #     [executor.submit(self.update_information_for_account, account["user"],
        #                      account["password"]) for account in list_account]


    def check_account_block(self):
        return False

    def check_block_type_function_load_comment(self, cookies):
        driver = setup_selenium_firefox()
        res = ""
        for _ in range(5):
            try:
                res = ""
                driver.get("https://www.facebook.com/")
                # cookies = self.token_and_cookies.load_cookies()
                cookies = cookies
                for each in cookies:
                    driver.add_cookie(each)
                driver.get("https://www.facebook.com/groups/phanbien/posts/2995815297152990/")
                break
            except Exception as e:
                print(f"Error in requests {e}")
                res = None
                continue
        if res is None:
            driver.close()
            return None
        time.sleep(3)
        box_menu = driver.find_element(By.CLASS_NAME,
                                            value="x6s0dn4 x78zum5 xdj266r x11i5rnm xat24cr x1mh8g0r xe0p6wg".replace(
                                                " ", "."))

        button_menu = box_menu.find_elements(By.CLASS_NAME,
                                             value="x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x1n2onr6 x87ps6o x1lku1pv x1a2a7pz".replace(
                                                 " ", "."))
        for each in button_menu:
            if each.get_attribute("role") == "button":
                each.click()
                break
        soup = BeautifulSoup(driver.page_source, "lxml")
        driver.close()
        if soup.find("div", class_="x6s0dn4 x78zum5 x2lah0s x1qughib x879a55 x1n2onr6") is not None:
            print("Block")
            return True
        print("Non Block")
        return False

    def run(self):
        print("Start thread manage account")
        while True:
            print("UPDATE ALL ACCOUNT")
            time.sleep(30*60)
            self.update_information_for_all_account()

    def get_all_account_active(self):
        return self.account_fb_collection.get_all_account_active()

    def get_random_account_active(self):
        return self.account_fb_collection.get_random_account_active()
