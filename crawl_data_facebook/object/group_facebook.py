import logging
import os
import json
import random
import re
import requests
import time
from queue import Queue
from threading import Thread
import concurrent.futures

from bs4 import BeautifulSoup

from database.facebook_db import FacebookCollection, TimePostUpdateCollection, AccountFacebookCollection
from config.config import Config
from utils.utils import setup_selenium_firefox

from threading import Lock
from object.post_group_facebook import PostGroupFacebook
from service.manage_account_facebook import ManageAccountFacebook


class GroupFacebook:

    def __init__(self, url, path_save_data):
        self.url_group = self.preprocess_url_group(url)
        self.config = Config()
        self.type = None
        self.id_group = None
        self.name_group = None
        self.logger = logging.getLogger(self.__class__.__name__)
        # self.token_and_cookies = token_and_cookies
        # self.token_and_cookies.get_token_and_cookies()
        self.account_col = AccountFacebookCollection()
        self.manage_account = ManageAccountFacebook()
        self.account_fb_for_group = self.account_col.get_random_account_active()
        self.get_id()
        self.get_name()
        self.next_page = ""
        self.path_save_data = path_save_data
        self.post_queue = Queue()
        self.post_id_crawled = []
        self.flag_post = False
        self.flag_update_token = False
        self.number_post = 0
        self.fb_data = FacebookCollection()
        self.time_post_update_collection = TimePostUpdateCollection()
        self.type = None
        self.queue_manage_crawler = Queue()
        self.lock_get_item_from_queue = Lock()

    def get_type(self):
        result_regex = re.search(r"https://www.facebook.com/groups/", self.url_group)
        if result_regex is not None:
            self.type = "group"
        else:
            self.type = "page"
        return self.type

    @staticmethod
    def preprocess_url_group(url_group):
        if url_group[-1] != "/":
            return url_group + "/"
        return url_group

    #   REQUEST GRAPH API GET INFORMATION OF GROUP
    def get_name(self):
        # url = f"https://graph.facebook.com/v15.0/{self.id_group}?" \
        #       f"access_token={self.token_and_cookies.load_token_access()}"
        url = f"https://graph.facebook.com/v15.0/{self.id_group}?" \
              f"""access_token={self.account_fb_for_group["token_access"]}"""
        requestJar = requests.cookies.RequestsCookieJar()
        for each in self.account_fb_for_group["cookies"]:
            # for each in self.token_and_cookies.load_cookies():

            requestJar.set(each["name"], each["value"])
        jsonformat = None
        for i in range(1000):
            try:
                response = requests.get(url, cookies=requestJar)
                jsonformat = json.loads(response.text)
                if self.check_token_valid(jsonformat):
                    continue
                break
            except:
                continue
        if jsonformat is None:
            return
        if "name" in jsonformat.keys():
            name_group = jsonformat["name"]
        else:
            name_group = "unknown"
        name_group = re.sub(r"[\\/*:?\"><|,]", "_", name_group)
        self.name_group = name_group
        return self.name_group

    # ACCESS GROUP AND GET ID OF GROUP
    def get_id(self):
        driver = setup_selenium_firefox()
        driver.get("https://www.facebook.com/")
        # cookies_file = self.token_and_cookies.load_cookies()
        cookies_file = self.account_fb_for_group["cookies"]
        for cook in cookies_file:
            driver.add_cookie(cook)
        driver.get("view-source:" + self.url_group)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "lxml")
        driver.close()
        string_ss = soup.text
        regex_page_id = re.search(r"(\"groupID\":\"\d+\")", string_ss)

        if regex_page_id is None:
            regex_page_id = re.search(r"(\"pageID\":\"\d+\")", string_ss)
        #
        # if regex_page_id is None:
        #     regex_page_id = re.search(r"(\"delegate_page\":{\"id\":\"\d+\"})", string_ss)

        start, end = regex_page_id.span()
        dict_id = string_ss[start:end]
        start_id, end_id = re.search(r"(:\"\d+\")", dict_id).span()
        id_objects = dict_id[start_id + 2: end_id - 1]
        self.id_group = id_objects
        return id_objects

    def load_post_id_have_crawled(self):
        # list_id = self.fb_data.get_list_id_for_page(self.name_group)

        # if not len(list_id):
        # if self.type == "page":
        #     list_id = [each.replace(".json", "") for each in
        #                os.listdir(self.path_save_data + self.name_group + "/text/")]
        # else:
        #     list_id = self.fb_data.get_list_id_for_page(self.name_group)
        #     if len(list_id)
        # # print(list_id)
        list_id = [each.replace(".json", "") for each in
                   os.listdir(self.path_save_data + self.name_group + "/text/")]
        self.post_id_crawled = list_id
        self.logger.info(f"NUMBER OF POST CRAWLED: {len(self.post_id_crawled)}")
        return self.post_id_crawled

    # REQUEST GRAPH API TO GET INFORMATION POST
    def request_first_page(self):
        # url = f"https://graph.facebook.com/v15.0/{self.id_group}/feed?" \
        #       f"&access_token={self.token_and_cookies.load_token_access()}&limit=100"
        # requestJar = requests.cookies.RequestsCookieJar()
        # for each in self.token_and_cookies.load_cookies():
        if self.type == "group":
            url = f"https://graph.facebook.com/v15.0/{self.id_group}/feed?" \
                  f"""&access_token={self.account_fb_for_group["token_access"]}&limit=100"""
        elif self.type == "page":
            url = f"https://graph.facebook.com/v15.0/{self.id_group}/posts?" \
                  f"""&access_token={self.account_fb_for_group["token_access"]}&limit=100"""
        requestJar = requests.cookies.RequestsCookieJar()
        for each in self.account_fb_for_group["cookies"]:
            requestJar.set(each["name"], each["value"])
        jsonformat = None
        for i in range(50):
            try:
                response = requests.get(url, cookies=requestJar)
                jsonformat = json.loads(response.text)
                if self.check_token_valid(jsonformat):
                    continue
                break
            except:
                continue
        if jsonformat is None:
            return
        try:
            self.next_page = jsonformat["paging"]["next"]
        except KeyError:
            self.next_page = None
        # print(jsonformat)
        try:
            for each in jsonformat["data"]:
                # print(each)
                if each["id"] in self.post_id_crawled:
                    continue
                id_post = each["id"]

                if self.type == "group":
                    updated_time = each["updated_time"]
                    post_new = {"_id": id_post, "updated_time": updated_time}
                    if self.time_post_update_collection.check_update_time(post_new):
                        # print("POST DOES NOT CHANGE")
                        # print("POST NO CHANGE")
                        continue
                else:
                    updated_time = each["created_time"]
                if self.config.interval_to_get_post is not None:
                    if not (self.check_time_post_update(updated_time)):
                        # print("POST TOO LONG")
                        continue
                postfb = PostGroupFacebook(self.url_group, id_post,
                                           self.path_save_data + self.name_group + "/", self.name_group)
                postfb.content = each["message"]
                if self.type == "group":
                    postfb.updated_time = updated_time
                else:
                    postfb.created_time = updated_time

                self.post_queue.put(postfb)
        except KeyError:
            pass
        return jsonformat

    # REQUEST GRAPH API TO GET INFORMATION POST
    def request_next_page(self):
        while self.next_page is not None:
            # requestJar = requests.cookies.RequestsCookieJar()
            # for each in self.token_and_cookies.load_cookies():
            requestJar = requests.cookies.RequestsCookieJar()
            for each in self.account_fb_for_group["cookies"]:
                requestJar.set(each["name"], each["value"])
            jsonformat = None
            for i in range(5):
                try:
                    response = requests.get(self.next_page, cookies=requestJar)
                    jsonformat = json.loads(response.text)
                    if self.check_token_valid(jsonformat):
                        continue
                    break
                except:
                    continue
            if jsonformat is None:
                continue
            try:
                self.next_page = jsonformat["paging"]["next"]
            except KeyError:
                self.next_page = None
            # print(jsonformat)
            try:
                for each in jsonformat["data"]:
                    if each["id"] in self.post_id_crawled:
                        continue
                    id_post = each["id"]

                    if self.type == "group":
                        updated_time = each["updated_time"]
                        post_new = {"_id": id_post, "updated_time": updated_time}
                        if self.time_post_update_collection.check_update_time(post_new):
                            # print("POST DOES NOT CHANGE")
                            # print("POST NO CHANGE")
                            continue
                    else:
                        updated_time = each["created_time"]
                    if self.config.interval_to_get_post is not None:
                        if not (self.check_time_post_update(updated_time)):
                            # print("POST TOO LONG")
                            continue
                    postfb = PostGroupFacebook(self.url_group, id_post,
                                               self.path_save_data + self.name_group + "/", self.name_group)
                    postfb.content = each["message"]
                    if self.type == "group":
                        postfb.updated_time = updated_time
                    else:
                        postfb.created_time = updated_time
                    self.post_queue.put(postfb)
            except KeyError:
                pass
        self.logger.info(f"NUMBER OF POST IN {self.name_group}: {self.post_queue.qsize()}")

    # CHECK RESULT FROM GRAPH API FACEBOOK
    @staticmethod
    def check_token_valid(jsonformat):
        if "error" in jsonformat.keys():
            if jsonformat["error"]["code"] == 102:
                # self.token_and_cookies.update_new_token()
                return True
            if jsonformat["error"]["code"] == 100:
                return False
            return False

    def create_folder_save_data(self):
        os.makedirs(self.path_save_data + self.name_group + "/", exist_ok=True)
        os.makedirs(self.path_save_data + self.name_group + "/text/", exist_ok=True)

    # CRAWLER POST
    def crawl_post(self):
        # CHECK ITEM IN QUEUES
        self.lock_get_item_from_queue.acquire()
        if not self.post_queue.qsize():
            self.lock_get_item_from_queue.release()
            self.queue_manage_crawler.get()
            return
        else:
            post_process = self.post_queue.get()
            self.lock_get_item_from_queue.release()
        # ASSIGN ACCOUNT FACEBOOK TO CRAWL POST
        account_facebook = self.account_col.get_account_to_crawl()
        if account_facebook is None:
            self.queue_manage_crawler.get()
            return
        post_process.account = account_facebook
        post_process.type = self.type
        print(account_facebook["user"])
        # PROCESS POST IN GROUP
        # try:
        if not post_process.process_post():
            postfb = PostGroupFacebook(self.url_group, post_process.id_post,
                                       self.path_save_data + self.name_group + "/", self.name_group)
            postfb.content = post_process.content
            self.post_queue.put(postfb)
        else:
            self.post_id_crawled.append(post_process.dict_post["_id"])
            self.number_post += 1
            self.account_col.update_status_account(account_facebook["user"], "active")

        # except Exception as e:
        #     print(f"Error external post {e}")
        #     print(post_process.id_post)
        #     try:
        #         post_process.driver.close()
        #     except:
        #         pass
        self.queue_manage_crawler.get()
        print("_____________________________________________")

    def get_list_random_account_facebook_active(self, number_crawler):
        list_account = self.manage_account.get_all_account_active()
        # print(f" LENGTH ACCOUNT IN DB {len(list_account)}")
        list_random_account = []
        for _ in range(number_crawler):
            account_select = list_account[random.randint(0, len(list_account) - 1)]
            list_random_account.append(account_select)
            list_account.remove(account_select)
        return list_random_account

    def thread_check_status(self):
        while (self.post_queue.qsize() > 0) or (self.next_page is not None):
            self.logger.info(f"NUMBER POST HAVE CRAWLED: {self.number_post}")
            self.logger.info(f"NUMBER POST IN QUEUES: {self.post_queue.qsize()}")
            time.sleep(60 * 30)

    def thread_manage_number_crawler(self):
        while (self.post_queue.qsize() > 0) or (self.next_page is not None):
            if self.queue_manage_crawler.qsize() < self.config.number_of_crawler:
                # print(f"NUMBER CRAWLER CURRENT {self.queue_manage_crawler.qsize()}")
                for _ in range(self.config.number_of_crawler):
                    if self.queue_manage_crawler.qsize() < self.config.number_of_crawler:
                        thread_request_next_page = Thread(target=self.crawl_post)
                        thread_request_next_page.start()
                        self.queue_manage_crawler.put(1)
            time.sleep(30)

    @staticmethod
    def process_time_updated(string_time):
        # print(string_time)
        regex_result = re.search(r"\+\d+", string_time)
        if regex_result is not None:
            start, end = regex_result.span()
            string_time = string_time[:start]
            return string_time
        return string_time

    def check_time_post_update(self, time_facebook):
        time_facebook = self.process_time_updated(time_facebook)
        time_facebook_tick = time.mktime(time.strptime(time_facebook, r"%Y-%m-%dT%H:%M:%S")) + 25200

        interval = (time.time() - time_facebook_tick)
        # print(interval)
        days = interval // 86400
        hour = interval % 86400 // 3600
        minute = interval % 86400 % 3600 // 60
        if int(interval) < self.config.interval_to_get_post:
            return True
        # print(f"POST TOO OLD {days} days {hour}hours {minute} minute")
        return False

    # PROCESS GROUP
    def process_group(self):
        print(self.url_group)
        self.get_type()
        print(self.type)
        # CHECK TIME POST SETTING TO CRAWL
        # if self.config.interval_to_get_post is not None:
        #     days = self.config.interval_to_get_post // 86400
        #     print(f"CRAWL POST IN RECENT {days} DAYS")
        # else:
        #     print(f"CRAWL ALL POST")
        # CREATE FOLDER SAVE DATA
        self.create_folder_save_data()
        # LOAD POST CRAWLED IN PAST
        self.load_post_id_have_crawled()
        # REQUEST FIRST PAGE GROUP TO GET LINK POST
        self.request_first_page()
        self.logger.info(f"CRAWL PAGE: {self.name_group}. ID PAGE: {self.id_group}")
        # THREAD REQUEST NEXT PAGE GROUP TO GET LINK POST
        thread_request_next_page = Thread(target=self.request_next_page)
        thread_request_next_page.start()
        # THREAD CHECK STATUS
        thread_status = Thread(target=self.thread_check_status)
        thread_status.start()
        time.sleep(60)
        # THREAD POOL CRAWLER (GET LINK IN QUEUE AND CRAWL)

        # while (self.post_queue.qsize() > 0) or (self.next_page is not None):
        #     try:
        #         list_account_facebook = self.get_list_random_account_facebook_active(self.config.number_of_crawler)
        #         print(f" LENGTH LIST ACCOUNT RANDOM: {len(list_account_facebook)}")
        #         if not len(list_account_facebook):
        #             continue
        #         with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.number_of_crawler) as executor:
        #             [executor.submit(self.crawl_post, account) for account in list_account_facebook]
        #         time.sleep(random.randint(1, 10))
        #     except:
        #         pass

        thread_manage_number_crawler = Thread(target=self.thread_manage_number_crawler)
        thread_manage_number_crawler.start()
        thread_request_next_page.join()
        thread_manage_number_crawler.join()
        # thread_manage_crawler.join()
        self.logger.info(f"FINISHED CRAWL PAGE {self.name_group}. NUMBER POST HAVE CRAWLED: {self.number_post}")
