import json
import re
import time
import logging
from threading import Thread
import os
import hashlib
import requests

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from object.class_facebook import ClassFacebook
from database.facebook_db import FacebookCollection, TimePostUpdateCollection
from service.manage_account_facebook import ManageAccountFacebook
from utils.utils import setup_selenium_firefox
from database.facebook_db import AccountFacebookCollection
from config.config import Config


class PostGroupFacebook:

    def __init__(self, url_page, id_post, path_save_data, name_page):
        self.class_facebook = ClassFacebook()
        self.config = Config()
        self.account = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.url_page = url_page
        self.name_page = name_page
        self.path_save_data = path_save_data
        self.id_post = id_post
        # self.token_and_cookies = token_and_cookies
        self.driver = None
        self.fb_data = FacebookCollection()
        self.content = None
        self.image = None
        self.link_image = []
        self.comment = []
        self.flag_driver = False
        self.flag_time_out = False
        self.number_comment = None
        self.manage_account = ManageAccountFacebook()
        self.created_time = None
        self.updated_time = None
        self.type = None
        self.url_post = None
        self.flag_time_out_load_all_comment = False
        self.account_col = AccountFacebookCollection()

    @staticmethod
    def preprocess_id_post(id_post):
        result_regex = re.search(r"\d_", id_post)
        if result_regex is not None:
            _, end = result_regex.span()
            id_post = id_post[end:]
        # print(id_post)
        return id_post

    def get_data_image_for_post(self):
        # url = f"https://graph.facebook.com/v15.0/{self.id_post}/attachments?" \
        #       f"access_token={self.token_and_cookies.load_token_access()}"
        url = f"https://graph.facebook.com/v15.0/{self.id_post}/attachments?" \
              f"""access_token={self.account["token_access"]}"""
        requestJar = requests.cookies.RequestsCookieJar()
        # for each in self.token_and_cookies.load_cookies():
        for each in self.account["cookies"]:
            requestJar.set(each["name"], each["value"])
        response = requests.get(url, cookies=requestJar)
        jsonformat = json.loads(response.text)
        return jsonformat

    def get_image_for_post(self):
        try:
            data_image = self.get_data_image_for_post()
        except:
            return self.link_image
        try:
            list_image = data_image["data"][0]["subattachments"]["data"][0]
            for each in list_image:
                self.link_image.append(each["media"]["image"]["src"])
            return self.link_image
        except:
            pass
        try:
            self.link_image.append(data_image["data"][0]["media"]["image"]["src"])
        except:
            pass
        return self.link_image

    def access_website(self):
        self.driver = setup_selenium_firefox()
        res = ""
        for _ in range(5):
            try:
                res = ""
                self.driver.get("https://www.facebook.com/")
                # cookies = self.token_and_cookies.load_cookies()
                cookies = self.account["cookies"]
                for each in cookies:
                    self.driver.add_cookie(each)
                if self.type == "group":
                    self.url_post = self.url_page + self.preprocess_id_post(self.id_post)
                elif self.type == "page":
                    self.url_post = self.url_page + "posts/" + self.preprocess_id_post(self.id_post)
                elif self.type == "video":
                    self.url_post = self.url_page
                self.driver.get(self.url_post)
                break
            except Exception as e:
                print(f"Error in requests {e}")
                res = None
                continue
        if res is None:
            self.driver.close()
            # self.driver.quit()
            return None
        # self.scroll(-10000)
        time.sleep(3)
        return self.parse_html()

    def parse_html(self):
        return BeautifulSoup(self.driver.page_source, "lxml")

    def select_mode_view_all_comment(self):
        try:
            box_menu = self.driver.find_element(By.CLASS_NAME,
                                                value=self.class_facebook.box_menu_select_mode_view.replace(" ", "."))
        except:
            self.account_col.update_status_account(self.account["user"], "active")
            return
        button_menu = box_menu.find_elements(By.CLASS_NAME, value=self.class_facebook.button_menu.replace(" ", "."))
        for each in button_menu:
            if each.get_attribute("role") == "button":
                if each.text is not None:
                    try:
                        element = self.driver.find_element(By.CLASS_NAME,
                                                       value=self.class_facebook.bar_like_comment_share.replace(" ", "."))
                        # self.driver.execute_script("arguments[0].scrollIntoView();", element)
                    except:
                        pass
                    self.scroll(-500)
                    time.sleep(1)
                    each.click()
                    break
        time.sleep(3)
        if self.check_block_type_function_load_comment():
            return "block"
        menu_item = self.driver.find_elements(By.CLASS_NAME, value=self.class_facebook.menu_item.replace(" ", "."))
        for each_item in menu_item:
            if re.search(r"Tất cả|All", each_item.text) is not None:
                # self.driver.execute_script("arguments[0].scrollIntoView();", each)
                try:
                    element = self.driver.find_element(By.CLASS_NAME,
                                                       value=self.class_facebook.bar_like_comment_share.replace(" ", "."))
                    self.driver.execute_script("arguments[0].scrollIntoView();", element)
                except:
                    pass
                self.scroll(-500)
                time.sleep(1)
                each_item.click()
                time.sleep(3)

    def show_all_comments(self):
        thread_time_out_load_comment = Thread(target=self.time_out_load_all_comment)
        thread_time_out_load_comment.start()
        box_total_comment = self.driver.find_element(By.CLASS_NAME,
                                                      value=self.class_facebook.box_total_comment.replace(" ", "."))
        list_button_more = box_total_comment.find_elements(By.CLASS_NAME,
                                                     value=self.class_facebook.list_button_more.replace(" ", "."))
        while len(list_button_more) > 0:
            if re.search(r"Xem|View|Views|^\d+ phản hồi|^\d (Replies|Reply)", list_button_more[-1].text,
                         flags=re.IGNORECASE) is None:
                if re.search(r"Xem|View|Views|^\d+ phản hồi|^\d (Replies|Reply)", list_button_more[0].text,
                             flags=re.IGNORECASE) is None:
                    # print("XXXXXXXX")
                    break
            for each in list_button_more:
                if self.flag_time_out_load_all_comment:
                    print("DONE LOAD COMMENT")
                    return
                try:
                    if re.search(r"Ẩn|Hide", each.text) is not None:
                        continue
                    each.click()
                    time.sleep(1)
                except:
                    continue
            time.sleep(5)

            for _ in range(5):
                try:
                    box_total_comment = self.driver.find_element(By.CLASS_NAME,
                                                                 value=self.class_facebook.box_total_comment.replace(
                                                                     " ", "."))
                    list_button_more = box_total_comment.find_elements(By.CLASS_NAME,
                                                                 value=self.class_facebook.list_button_more.replace(
                                                                     " ", "."))
                    self.scroll(1000)
                except:
                    time.sleep(1)
                    continue
        print("DONE LOAD COMMENT")

        # print("DONE LOAD ALL COMMENT")

    def scroll(self, pixel):
        javascript = f"window.scrollBy(0,{pixel});"
        self.driver.execute_script(javascript)

    def show_more_text(self):
        box_total_comment = self.driver.find_element(By.CLASS_NAME,
                                                      value=self.class_facebook.box_total_comment.replace(" ", "."))
        list_button_more_text = box_total_comment.find_elements(By.CLASS_NAME,
                                                          value=self.class_facebook.list_button_more_text.replace(
                                                              " ", "."))
        while len(list_button_more_text):
            for each in list_button_more_text:
                try:
                    if each.get_attribute("role") == "button":
                        if re.search(r"Xem thêm|See more", each.text) is None:
                            continue
                        each.click()
                        self.scroll(1000)
                except:
                    pass
            number_button_more_old = len(list_button_more_text)

            box_total_comment = self.driver.find_element(By.CLASS_NAME,
                                                         value=self.class_facebook.box_total_comment.replace(" ", "."))
            list_button_more_text = box_total_comment.find_elements(By.CLASS_NAME,
                                                                    value=self.class_facebook.list_button_more_text.
                                                                    replace(" ", "."))
            if number_button_more_old == len(list_button_more_text):
                break
            # time.sleep(2)

    def get_content(self):
        soup = self.parse_html()
        content = ""
        content_tag = soup.find("div", class_="x1swvt13 x1l90r2v x1pi30zi x1iorvi4")
        if content_tag is not None:
            print("CONTENT TYPE 1")
            paragraph_content_tag = content_tag.find_all("div", attrs={"style": "text-align: start;"})
            print(f"NUMBER PARAGRAHPH {len(paragraph_content_tag)}")
            if len(paragraph_content_tag):
                for each in paragraph_content_tag:
                    content += each.get_text(strip=False).strip() + "\n"
            content = content_tag.get_text(strip=False, separator="\n")
            return content.strip()
        content_tag_new = soup.find_all("div", class_="x1iorvi4 x1pi30zi x1l90r2v x1swvt13")
        if len(content_tag_new):
            print("CONTENT TYPE 2")
            for each in content_tag_new:
                content += each.get_text(strip=False).strip() + "\n"
            return content.strip()

        content_tag_new = soup.find_all("span",
                                        class_="x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x3x7a5m x1f6kntn xvq8zen xo1l8bm xzsf02u x1yc453h")

        if len(content_tag_new):
            print("CONTENT TYPE 3")
            for each in content_tag_new:
                content += each.get_text(separator="\n", strip=True) + "\n"
            return content.strip()
        content_tag_new = soup.find("span",
                                    class_="x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xudqn12 x3x7a5m x6prxxf xvq8zen xo1l8bm xzsf02u x1yc453h")
        if content_tag_new is not None:
            print("CONTENT TYPE 4")
            content = content_tag_new.get_text(separator="\n", strip=True)
            return content
        return content

    def get_request_content(self):
        url = f"https://graph.facebook.com/v15.0/{self.id_post}?" \
              f"""access_token={self.account["token_access"]}"""
        requestJar = requests.cookies.RequestsCookieJar()
        # for each in self.token_and_cookies.load_cookies():
        for each in self.account["cookies"]:
            requestJar.set(each["name"], each["value"])
        response = None
        for _ in range(10):
            try:
                response = requests.get(url, cookies=requestJar)
                break
            except:
                pass
        if response is None:
            return False
        jsonformat = json.loads(response.text)
        return jsonformat

    def get_content_2(self):
        data = self.get_request_content()
        # print(data)
        if not data:
            return
        if self.type == "video":
            self.content = data["description"]
            self.updated_time = data["updated_time"]
        else:
            self.content = data["message"]
            self.created_time = data["created_time"]

    def get_number_comment(self):
        soup = self.parse_html()
        # box_post = soup.find("div", class_= self.class_facebook.box_post)

        box_number_comment = soup.find("div", class_=self.class_facebook.box_number_comment)
        if box_number_comment is None:
            return None
        box_text = box_number_comment.find("span",
                                           class_=self.class_facebook.box_text_number_comment_1)
        if box_text is None:
            box_text = box_number_comment.find("span",
                                               class_=self.class_facebook.box_text_number_comment_2)
        if box_text is None:
            return None
        text_number_comment = box_text.text
        result_regex = re.search(r"\d+,?\d?K|\d+", text_number_comment)
        if result_regex is None:
            return None
        start, end = result_regex.span()
        return text_number_comment[start:end].strip()

    @staticmethod
    def check_number_comment_more_2k(text_number_comment):
        text_number_comment = str(text_number_comment)
        result_regex = re.search(r"\d+,\d", text_number_comment)
        if result_regex is None:
            result_regex = re.search(r"\d+", text_number_comment)
            if result_regex is None:
                return True
            start, end = result_regex.span()
            # text_number_comment = text_number_comment[strat:end]
            if int(text_number_comment[start:end]) > 2:
                print("MORE 2k")
                print(f"NUMBER COMMENT {int(text_number_comment[start:end])}")
                return True
        start, end = result_regex.span()
        text_number_comment = text_number_comment[start:end]
        # print(text_number_comment)
        result_regex = re.search(r"\d+,?", text_number_comment)
        if result_regex is None:
            return True
        start, end = result_regex.span()
        number_first = text_number_comment[start:end - 1]
        second_first = text_number_comment[end:]
        # print(number_first)
        if int(number_first) > 2:
            # print("MORE 2k")
            # print(f"NUMBER COMMENT {number_first}")
            return True
        # print(second_first)
        if int(second_first) > 5:
            # print("MORE 1.5k")
            # print(f"NUMBER COMMENT {text_number_comment}")
            return True
        # print(f"NUMBER COMMENT {text_number_comment}")
        # print("less 1.5k")
        return False

    def get_data_for_box_comment(self, box_comment):
        user_comment = box_comment.find("span", class_=self.class_facebook.user_comment)
        if user_comment is None:
            return None
        text_comment = self.get_text_for_box_comment(box_comment)
        tags = self.get_tags_for_box_comment(box_comment)
        attachment = self.get_attachment_for_box_comment(box_comment)
        link_to_reply = self.get_link_to_reply(box_comment)
        data = {"user": user_comment.text, "attachment": attachment, "text": text_comment,
                "tags": tags, "link_to_reply": link_to_reply}
        return data

    def get_link_to_reply(self, box_comment):
        box_link = box_comment.find("a",
                                    class_=self.class_facebook.box_link)
        if box_link is None:
            return None
        link_to_reply = box_link.get("href")
        # print(link_to_reply)
        return link_to_reply

    def get_attachment_for_box_comment(self, box_comment):
        box_attachment = box_comment.findChild("div", class_=self.class_facebook.box_attachment, recursive=False)
        data_image = None
        data_link = None
        if box_attachment is None:
            return {"image": data_image, "link": data_link}
        box_image_attachment = box_attachment.find("a", class_=self.class_facebook.box_image_attachment)
        box_link_attachment = box_attachment.find("a", class_=self.class_facebook.box_link_attachment)
        if box_image_attachment is not None:
            image_element = box_image_attachment.find("img")
            if image_element is not None:
                image_source = image_element["src"]
                image_download = self.save_image(image_source)
                if image_download:
                    image_description = image_element["alt"]
                    data_image = {"source": image_download, "description": image_description}

        if box_link_attachment is not None:
            link_element = box_link_attachment.find("span")
            if link_element is not None:
                link = box_link_attachment["href"]
                link_description = link_element.text
                data_link = {"source": link, "description": link_description}
        return {"image": data_image, "link": data_link}

    def save_image(self, src_image):
        path_image = self.path_save_data + "image/" + self.id_post + "/"
        try:
            os.makedirs(path_image, exist_ok=True)
        except:
            pass
        id_image = hashlib.md5(src_image.encode("utf-8")).hexdigest()
        filename = self.path_save_data + "image/" + self.id_post + "/" + id_image + '.jpg'
        # print(filename)
        for _ in range(5):
            try:
                with open(filename, 'wb') as f:
                    f.write(requests.get(src_image).content)
                return id_image
            except:
                return False

    def get_text_for_box_comment(self, box_text_comment):
        text_main_comment_box = box_text_comment.find("div", class_=self.class_facebook.text_main_comment_box_1)
        text_comment = ""
        if text_main_comment_box is None:
            text_main_comment_box = box_text_comment.find("div", class_=self.class_facebook.text_main_comment_box_2)
        if text_main_comment_box is None:
            return None
        list_paragraph_element = text_main_comment_box.findAll("div", attrs={"style": "text-align: start;"})
        for each in list_paragraph_element:
            text_comment += each.get_text(strip=False) + "\n"
        return text_comment.strip()

    def get_tags_for_box_comment(self, box_text_comment):
        tags = []
        text_main_comment_box = box_text_comment.find("div", class_=self.class_facebook.text_main_comment_box_1)
        if text_main_comment_box is None:
            text_main_comment_box = box_text_comment.find("div", class_=self.class_facebook.text_main_comment_box_2)
        if text_main_comment_box is None:
            return tags
        tags_element = box_text_comment.findAll("a",
                                                class_=self.class_facebook.tag_elements)
        for tag in tags_element:
            tags.append(tag.text)
        return tags

    def get_all_comment_in_post(self):
        soup = self.parse_html()
        box_total_comment = soup.find("div", class_=self.class_facebook.box_total_comment)
        box_total_comment = box_total_comment.findChild("ul", recursive=False)
        if box_total_comment is None:
            return []
        list_comment = box_total_comment.findChildren("li", recursive=False)
        list_total_comment = []
        for each_comment in list_comment:
            data_each_comment = self.get_data_for_each_comment(each_comment)
            if data_each_comment is None:
                continue
            list_total_comment.append(data_each_comment)
        return list_total_comment

    def get_data_for_each_comment(self, box_each_comment):
        main_comment = self.get_main_comment(box_each_comment)
        if main_comment is None:
            return None
        list_reply = self.get_main_reply(box_each_comment)
        main_comment["replies"] = list_reply
        return main_comment

    def get_main_comment(self, box_comment):
        big_box_main_comment = box_comment.find("div", class_=self.class_facebook.big_box_main_comment)
        small_box_main_comment = big_box_main_comment.find("div", class_=self.class_facebook.small_box_main_comment)
        main_comment = self.get_data_for_box_comment(small_box_main_comment)
        if main_comment is None:
            return None
        return main_comment

    def get_main_reply(self, box_main_reply):
        list_reply = []
        total_box_reply = box_main_reply.find("div", class_=self.class_facebook.total_box_reply_1)
        if total_box_reply is None:
            total_box_reply = box_main_reply.find("div", class_=self.class_facebook.total_box_reply_2)
        if total_box_reply is None:
            return list_reply
        total_box_reply = total_box_reply.find("ul")
        if total_box_reply is None:
            return list_reply
        list_main_reply_tag = total_box_reply.findChildren("li", recursive=False)

        for each_main_reply in list_main_reply_tag:
            big_box_main_reply = each_main_reply.find("div", class_=self.class_facebook.big_box_main_reply_1)
            if big_box_main_reply is None:
                big_box_main_reply = each_main_reply.find("div",
                                                          class_=self.class_facebook.big_box_main_reply_2)
            if big_box_main_reply is None:
                continue
            tag_main_reply = big_box_main_reply.find("div", class_=self.class_facebook.small_box_main_reply)
            main_reply = self.get_data_for_box_comment(tag_main_reply)
            if main_reply is None:
                continue
            box_mini_reply = big_box_main_reply.find_next_sibling("div")
            if box_mini_reply is None:
                main_reply["replies"] = []
                list_reply.append(main_reply)
                continue
            mini_reply = self.get_mini_reply(box_mini_reply)
            main_reply["replies"] = mini_reply
            list_reply.append(main_reply)
        return list_reply

    def get_mini_reply(self, box_mini_reply):
        list_mini_reply = []
        reply_tag = box_mini_reply.find("ul")
        if reply_tag is None:
            return list_mini_reply
        list_mini_reply_tag = reply_tag.findAll("li")
        for each in list_mini_reply_tag:
            big_box_mini_reply = each.find("div",
                                       class_=self.class_facebook.big_box_mini_reply)
            if big_box_mini_reply is None:
                continue
            tag_mini_reply = big_box_mini_reply.find("div", class_=self.class_facebook.small_box_mini_reply)
            if tag_mini_reply is None:
                continue
            mini_reply = self.get_data_for_box_comment(tag_mini_reply)
            if mini_reply is None:
                continue
            list_mini_reply.append(mini_reply)
        return list_mini_reply

    def check_block_type_function_load_comment(self):
        soup = self.parse_html()
        # print(soup.text)
        if soup.find("div", class_=self.class_facebook.block_function_load_comment) is not None:
            self.account_col.update_status_account(self.account["user"], "temporary inactive")
            return True
        return False

    def check_block_type_account(self):
        soup = self.parse_html()
        if soup.find("div",
                     class_=self.class_facebook.block_account) is not None:
            self.account_col.update_status_account(self.account["user"], "account block")
            # self.manage_account.update_status(self.account["user"], "account block")
            return True
        return False

    def time_out_for_driver(self):
        for _ in range(5):
            if self.flag_time_out:
                self.flag_driver = True
                return
            time.sleep(300)
        self.flag_driver = True

    def close_driver(self):
        thread_time_out = Thread(target=self.time_out_for_driver)
        thread_time_out.start()
        while True:
            if self.flag_driver:
                self.driver.close()
                # self.driver.quit()
                # print(f"CLOSE SELENIUM FOR {self.url_page + self.preprocess_id_post(self.id_post)}")
                break
            time.sleep(30)

    def time_out_load_all_comment(self):
        for _ in range(self.config.time_for_load_comment):
            time.sleep(60)
            if self.flag_time_out_load_all_comment:
                return
        self.flag_time_out_load_all_comment = True
        print("INTERRUPT LOAD ALL COMMENT")

    @property
    def dict_post(self):
        return {"_id": self.id_post,
                "url_post": self.url_post,
                "name_page": self.name_page,
                "created_time": self.created_time,
                "updated_time": self.updated_time,
                "image": self.link_image,
                "content": self.content,
                "number_comment": self.number_comment,
                "comment": self.comment}

    def save_text(self):
        file_data_folder = self.path_save_data + "text/" + self.id_post
        path_text = self.path_save_data + "text/"
        os.makedirs(path_text, exist_ok=True)
        json.dump(self.dict_post, open(file_data_folder + ".json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=4)

    @property
    def dict_time_update_post(self):
        return {"_id": self.id_post,
                "updated_time": self.updated_time}

    def save_updated_time_post(self):
        # print("FUNCTION UPDATE POST")
        time_post_update_db = TimePostUpdateCollection()
        time_post_new = self.dict_time_update_post
        time_post_update_db.update_time_for_post(time_post_new)
        # print("UPDATE SUCCESSFUL ")

    def process_post(self):
        time_before = time.time()
        # print(f"B1 {time.time()-time_before}")
        try:
            # time_before = time.time()
            # GET CONTENT FROM GRAPH API
            self.get_content_2()
            # GET IMAGE FROM GRAPH API

            # print(f"B2 {time.time() - time_before}")
            # time_before = time.time()

            self.get_image_for_post()

            # ACCESS POST BY SELENIUM

            # print(f"B3 {time.time() - time_before}")
            # time_before = time.time()

            if self.access_website() is None:
                self.account_col.update_status_account(self.account["user"], "active")
                return False

            # THREAD CHECK BROWSER NOT WORKING (BROWSER WILL EXIST IN 20 MINUTES)
            thread_check_not_working = Thread(target=self.close_driver)
            thread_check_not_working.start()

            self.number_comment = self.get_number_comment()
            # if self.check_number_comment_more_2k(self.number_comment):
            #     self.flag_driver = True
            #     self.flag_time_out = True
            #     return True
            # CHECK ACCOUNT BLOCK

            # print(f"B4 {time.time()-time_before}")
            # time_before = time.time()

            if self.check_block_type_account():
                self.flag_driver = True
                self.flag_time_out = True
                return False
            self.scroll(300)
        except:
            self.flag_driver = True
            self.flag_time_out = True
            self.account_col.update_status_account(self.account["user"], "active")
            return False

        # print(f"B5 {time.time() - time_before}")
        # time_before = time.time()

        # print(self.url_page + self.preprocess_id_post(self.id_post))
        # GET COMMENT
        try:
            # print(f"B6 {time.time() - time_before}")
            # time_before = time.time()
            if self.select_mode_view_all_comment() == "block":
                self.flag_driver = True
                self.flag_time_out = True
                return False
            time.sleep(5)

            # print(f"B7 {time.time() - time_before}")
            # time_before = time.time()
            self.show_all_comments()
            self.flag_time_out_load_all_comment = True
            # print(f"B8 {time.time() - time_before}")
            # time_before = time.time()
            self.show_more_text()
        except Exception as e:
            # self.manage_account.update_status(self.account["user"], "active")
            print(f"Error internal post {e} \n {self.url_post}, {self.id_post}")
            self.flag_driver = True
            self.flag_time_out = True
            self.account_col.update_status_account(self.account["user"], "active")
            return False
        # self.manage_account.update_status(self.account["user"], "active")
        # print(f"B9 {time.time() - time_before}")
        # time_before = time.time()
        image_post = []
        for each in self.link_image:
            image_download = self.save_image(each)
            if image_download:
                image_post.append(image_download)

        self.link_image = image_post
        self.comment = self.get_all_comment_in_post()
        self.save_text()
        if self.type == "group":
            self.save_updated_time_post()

        self.flag_driver = True
        self.flag_time_out = True
        print(f"Done :{time.time()-time_before}")
        return True
