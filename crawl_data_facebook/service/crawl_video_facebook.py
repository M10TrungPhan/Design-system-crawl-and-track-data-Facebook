import threading
import time
import os
import concurrent.futures
import re
import logging
import random

from threading import Lock
from queue import Queue
from object.class_facebook import ClassFacebook
from bs4 import BeautifulSoup
from database.facebook_db import AccountFacebookCollection, TimePostUpdateCollection
from utils.utils import setup_selenium_firefox
from object.post_group_facebook import PostGroupFacebook
from config.config import Config


class CrawlVideoFacebookService:

    def __init__(self, username, path_save_data):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.account_col = AccountFacebookCollection()
        self.class_facebook = ClassFacebook()
        self.config = Config()
        self.account_scrape_video = username
        self.driver = None
        self.path_save_data = path_save_data
        self.post_id_crawled = []
        self.queue_video_1 = Queue()
        self.queue_video_2 = Queue()
        self.flag_red = False
        self.number_post = 0
        self.queue_manage_crawler = Queue()
        self.name_page = "watch_facebook"
        self.lock_get_queue_video_2 = Lock()
    # def get_account_scrape_video(self, username):
    #     return self.account_col.query_account_follow_username(username)

    def access_watch_facebook(self):
        account_scrape_video = self.account_col.query_account_follow_username(self.account_scrape_video)
        self.driver = setup_selenium_firefox()
        res = None
        for _ in range(5):
            try:
                res = "None"
                self.driver.get("https://www.facebook.com")

                cookies = account_scrape_video["cookies"]
                for each in cookies:
                    self.driver.add_cookie(each)
                self.driver.get("https://www.facebook.com/watch")
                break
            except Exception as e:
                print(f"Error in requests {e}")
                res = None
                continue
        if res is None:
            self.driver.close()
            return None
        time.sleep(3)
        return self.parse_html(self.driver)

    @staticmethod
    def parse_html(driver):
        return BeautifulSoup(driver.page_source, "lxml")

    def scroll(self, pixel):
        javascript = f"window.scrollBy(0,{pixel});"
        self.driver.execute_script(javascript)

    def create_folder_save_data(self):
        os.makedirs(self.path_save_data + self.name_page + "/", exist_ok=True)
        os.makedirs(self.path_save_data + self.name_page + "/text/", exist_ok=True)
        os.makedirs(self.path_save_data + self.name_page + "/image/", exist_ok=True)

    def load_post_id_have_crawled(self):
        list_id = [each.replace(".json", "") for each in os.listdir(self.path_save_data + "watch_facebook" + "/text/")]
        self.post_id_crawled = list_id
        self.logger.info(f"NUMBER OF POST CRAWLED: {len(self.post_id_crawled)}")
        return self.post_id_crawled

    def get_link_video_in_page(self):
        soup = self.parse_html(self.driver)
        list_link_video = []
        list_element_link = soup.find_all("a", class_=self.class_facebook.box_link_to_video)
        for each in list_element_link:
            if each.get("aria-label") is not None:
                link_video_facebook = each.get("href")
                if "https://www.facebook.com" not in link_video_facebook:
                    link_video_facebook = "https://www.facebook.com" + link_video_facebook
                list_link_video.append(link_video_facebook)
        return list_link_video

    def get_all_video_watch_for_account(self):
        list_video_watch_of_account = []
        self.access_watch_facebook()
        while len(list_video_watch_of_account) < self.config.number_video_crawl:
            self.scroll(10000)
            time.sleep(random.randint(1, 10))
            for each in self.get_link_video_in_page():
                if each not in list_video_watch_of_account:
                    list_video_watch_of_account.append(each)
                    # print(each)
                    self.queue_video_1.put(each)
        self.flag_red = True
        print("DONE get_all_video_watch_for_account ")
        # self.driver.close()

    def access_and_process_link_video_raw(self):
        if not(self.queue_video_1.qsize()):
            return
        # account = self.account_col.get_random_account_active()
        link_raw_video = self.queue_video_1.get()
        driver = setup_selenium_firefox()
        # cookies = account["cookies"]
        # driver.get("https://www.facebook.com/watch")
        # for each in cookies:
        #     driver.add_cookie(each)
        driver.get(link_raw_video)
        time.sleep(3)
        current_url = driver.current_url
        soup = self.parse_html(driver)
        link_new = soup.find("a", class_=self.class_facebook.box_link)
        if link_new is None:
            driver.close()
            return
        link_new = link_new.get("href")
        id_video = self.get_id_video_from_url(current_url)
        # driver.get(link_new)
        driver.close()
        if id_video in self.post_id_crawled:
            return
        if not id_video or (link_new is None):
            return
        self.queue_video_2.put((link_new, id_video))

    def thread_access_and_process_link_video_raw(self):
        while (self.queue_video_1.qsize()) or (not self.flag_red):
            # print("XXXXXXXXXXXXXXXXXX")
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                [executor.submit(self.access_and_process_link_video_raw) for _ in range(3)]
            time.sleep(random.randint(1, 10))
            # print(f"QUEUE VIDEO 1:{self.queue_video_1.qsize()}")
            # print(f"QUEUE VIDEO 2: {self.queue_video_2.qsize()}")
        print(f"QUEUE VIDEO 1:{self.queue_video_1.qsize()}")
        print(f"QUEUE VIDEO 2: {self.queue_video_2.qsize()}")
        print("DONE thread_access_and_process_link_video_raw ")

    @staticmethod
    def get_id_video_from_url(link_video):
        regex_result = re.search(r"\?v=\d+|videos/\d+", link_video)
        if regex_result is None:
            return False
        start, end = regex_result.span()
        string_contain_id_video = link_video[start:end]
        regex_result = re.search(r"\d+", string_contain_id_video)
        if regex_result is None:
            return False
        start, end = regex_result.span()
        return string_contain_id_video[start:end]

    def crawl_post(self):
        # CHECK ITEM IN QUEUES
        self.lock_get_queue_video_2.acquire()
        if not self.queue_video_2.qsize():
            self.queue_manage_crawler.get()
            self.lock_get_queue_video_2.release()
            return
        else:
            link_video, id_video = self.queue_video_2.get()
        self.lock_get_queue_video_2.release()
        account_facebook = self.account_col.get_account_to_crawl()
        if account_facebook is None:
            self.queue_manage_crawler.get()
            return
        video_process = PostGroupFacebook(link_video, id_video, self.path_save_data +
                                          self.name_page + "/", self.name_page)
        video_process.account = account_facebook
        # ASSIGN ACCOUNT FACEBOOK TO CRAWL POST
        # print(link_video, id_video)
        print(account_facebook["user"], link_video)
        video_process.type = "video"
        # self.manage_account.update_status(account_facebook["user"], "in process")
        # PROCESS POST IN GROUP

        if not video_process.process_post():
            print("CRAWL FAILED")
        #     postfb = PostGroupFacebook(self.url_group, post_process.id_post,
        #                                self.path_save_data + self.name_group + "/", self.name_group)
        #     postfb.content = post_process.content
        #     self.post_queue.put(postfb)
        else:
            print("SUCCESS CRAWL")
            self.account_col.update_status_account(account_facebook["user"], "active")
            self.post_id_crawled.append(video_process.dict_post["_id"])
            self.number_post += 1
        self.queue_manage_crawler.get()
        print("_____________________________________________")

    def thread_manage_number_crawler(self):
        while (self.queue_video_2.qsize()) or (self.queue_video_1.qsize()):
            if self.queue_manage_crawler.qsize() < self.config.number_of_crawler_video:
                # print("XXXXXXXXXXXX")
                # print(f"NUMBER CRAWLER CURRENT {self.queue_manage_crawler.qsize()}")
                for _ in range(2):
                    if self.queue_manage_crawler.qsize() < self.config.number_of_crawler_video:
                        thread_request_next_page = threading.Thread(target=self.crawl_post)
                        thread_request_next_page.start()
                        self.queue_manage_crawler.put(1)
            time.sleep(random.randint(1, 10))
        print("DONE THREAD CRAWLER")

    def process_video_facebook(self):
        self.create_folder_save_data()
        self.load_post_id_have_crawled()
        print(len(self.post_id_crawled))
        thread_get_all_video_watch = threading.Thread(target=self.get_all_video_watch_for_account)
        thread_get_all_video_watch.start()
        time.sleep(20)
        thread_access_process_link = threading.Thread(target=self.thread_access_and_process_link_video_raw)
        thread_access_process_link.start()
        thread_manage_number_crawler = threading.Thread(target=self.thread_manage_number_crawler)
        time.sleep(40)
        thread_manage_number_crawler.start()
        thread_get_all_video_watch.join()
        thread_access_process_link.join()
        thread_manage_number_crawler.join()
        print("DONE GET DATA VIDEO WATCH")
        print(f"NUMBER VIDEO CRAWLED IS {self.number_post}")


if __name__ == "__main__":
    for _ in range(20):
        crawl_watch = CrawlVideoFacebookService("txnnxt2k@gmail.com", r"E:/test_watch_facebook/")
        crawl_watch.process_video_facebook()
        time.sleep(60)

    # account_col = AccountFacebookCollection()
    # id_post = "852745799109961"
    # url = "https://www.facebook.com/Theanh28/posts/pfbid0r1bSbSdxBGHfVbZ3vqnCmsfBi9B6GNGMsJLXYeKkQQBvAySTY55C7WrgZg7TuweUl?comment_id=558742355763204&__tn__=R"
    # postfb = PostGroupFacebook(url, id_post,  r"E:/test_watch_facebook/", "watch_facebook")
    # postfb.type = "video"
    # postfb.account = account_col.get_account_to_crawl()
    # postfb.process_post()

















