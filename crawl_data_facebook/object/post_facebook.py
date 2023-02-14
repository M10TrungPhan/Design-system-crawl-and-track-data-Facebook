import json
import concurrent.futures
import requests
import logging

from object.token_and_cookies import TokenAndCookies
from object.comment_facebook import CommentFacebook
from database.facebook_db import FacebookCollection


class PostFacebook:

    def __init__(self, id_post, token_and_cookies: TokenAndCookies, path_save_data, name_page):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.name_page = name_page
        self.path_save_data = path_save_data
        self.id_post = id_post
        self.token_and_cookies = token_and_cookies
        self.next_post = ""
        self.content = None
        self.image = None
        self.fb_data = FacebookCollection()
        self.link_image = []
        self.comment = []
        self.comment_after_process = []

    def get_image_for_post(self):
        url = f"https://graph.facebook.com/v15.0/{self.id_post}/attachments?" \
              f"access_token={self.token_and_cookies.load_token_access()}"
        requestJar = requests.cookies.RequestsCookieJar()
        for each in self.token_and_cookies.load_cookies():
            requestJar.set(each["name"], each["value"])
        response = requests.get(url, cookies=requestJar)
        jsonformat = json.loads(response.text)
        try:
            self.link_image.append(jsonformat["data"][0]["media"]["image"]["src"])
        except:
            pass

    def request_first_post(self):
        url = f"https://graph.facebook.com/v15.0/{self.id_post}/comments?filter=stream" \
              f"&access_token={self.token_and_cookies.load_token_access()}"
        requestJar = requests.cookies.RequestsCookieJar()
        for each in self.token_and_cookies.load_cookies():
            requestJar.set(each["name"], each["value"])
        jsonformat = None

        for i in range(5):
            try:
                response = requests.get(url, cookies=requestJar)
                jsonformat = json.loads(response.text)
                if self.check_token_valid(jsonformat):
                    continue
                break
            except:
                continue

        if jsonformat is None:
            self.next_post = None
            return
        try:
            self.next_post = jsonformat["paging"]["next"]
        except KeyError:
            self.next_post = None
        try:
            for each in jsonformat["data"]:
                commentfb = CommentFacebook(each["id"], self.token_and_cookies)
                commentfb.main_comment = each["message"]
                commentfb.user_comment = each["from"]["name"]
                self.comment.append(commentfb)
        except KeyError:
            pass
        return jsonformat

    def request_next_post(self):
        while self.next_post is not None:
            requestJar = requests.cookies.RequestsCookieJar()
            for each in self.token_and_cookies.load_cookies():
                requestJar.set(each["name"], each["value"])
            jsonformat = None
            for i in range(5):
                try:
                    response = requests.get(self.next_post, cookies=requestJar)
                    jsonformat = json.loads(response.text)
                    if self.check_token_valid(jsonformat):
                        continue
                    break
                except:
                    continue
            if jsonformat is None:
                return
            try:
                self.next_post = jsonformat["paging"]["next"]
            except KeyError:
                self.next_post = None
            try:
                for each in jsonformat["data"]:
                    commentfb = CommentFacebook(each["id"], self.token_and_cookies)
                    commentfb.main_comment = each["message"]
                    commentfb.user_comment = each["from"]["name"]
                    self.comment.append(commentfb)
            except KeyError:
                pass

    def check_token_valid(self, jsonformat):
        if "error" in jsonformat.keys():
            if jsonformat["error"]["code"] == 102:
                self.token_and_cookies.update_new_token()
                return True
            if jsonformat["error"]["code"] == 100:
                return False
            return False

    @property
    def dict_post(self):
        return {"_id": self.id_post,
                "name_page": self.name_page,
                "image": self.link_image,
                "content": self.content,
                "comment": self.comment_after_process}

    @staticmethod
    def thread_process_comment(object_comment):
        return object_comment.process_comment()

    def process_post(self):
        self.get_image_for_post()
        self.request_first_post()
        self.request_next_post()
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(self.thread_process_comment, each) for each in self.comment]
            for result in futures:
                self.comment_after_process.append(result.result())
        json.dump(self.dict_post, open(self.path_save_data + self.id_post+".json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=4)
        # self.fb_data.save_data(self.dict_post)
        return True
