import os
import logging
from threading import Thread
import re

from service.manage_account_facebook import ManageAccountFacebook
from object.page_facebook import PageFacebook
from object.group_facebook import GroupFacebook
from object.token_and_cookies import TokenAndCookies
from config.config import Config


class CrawlFacebook(Thread):

    def __init__(self, url):
        super(CrawlFacebook, self).__init__()
        self.config = Config()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.token_and_cookies = TokenAndCookies()
        self.url = url
        self.path_save_data = self.config.path_save_data
        self.type = None

    def create_folder_save_data(self):
        os.makedirs(self.path_save_data + "/", exist_ok=True)

    def get_type(self):
        result_regex = re.search(r"https://www.facebook.com/groups/", self.url)
        if result_regex is not None:
            self.type = "group"
        else:
            self.type = "page"
        return self.type

    def run(self):
        self.logger.info(f"START CRAWL {self.url}")
        # self.get_type()
        # if self.type == "group":
        #     group = GroupFacebook(self.url, self.path_save_data)
        #     group.process_group()
        # else:
        #     page = PageFacebook(self.url, self.token_and_cookies, self.path_save_data)
        #     page.process_page()
        group = GroupFacebook(self.url, self.path_save_data)
        group.process_group()
        self.logger.info(f"FINISHED CRAWL {self.url}")
