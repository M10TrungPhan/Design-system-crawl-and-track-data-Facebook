import time
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import re
import pymongo
import random
from object.class_facebook import ClassFacebook

from bs4 import BeautifulSoup
from utils.utils import setup_selenium_firefox


class GetDialogue:

    def __init__(self, url_dialogue, main_reply):
        self.url_dialogue = url_dialogue
        self.main_reply = main_reply
        self.driver = None
        self.clas_facebook = ClassFacebook()

    @staticmethod
    def get_random_account_active():
        client = pymongo.MongoClient(host="172.29.13.23", port=20253, username="admin", password="admin")
        database = client["facebook"]
        facebook_col = database["account_fb"]
        myquery = {"status": "active"}
        list_account = []
        for x in facebook_col.find(myquery):
            list_account.append(x)
        return list_account[random.randint(0, len(list_account) - 1)]

    @staticmethod
    def process_link_reply(link_reply):
        regex_result = re.search(r"\?comment_id=\d+&reply_comment_id=\d+", link_reply)
        if regex_result is not None:
            start, end = regex_result.span()
            return link_reply[:end]
        return link_reply

    def access_url_comment(self, url_comment):
        account = self.get_random_account_active()
        self.driver = setup_selenium_firefox()
        res = ""
        for _ in range(5):
            try:
                res = ""
                self.driver.get("https://www.facebook.com/")
                cookies = account["cookies"]
                for cook in cookies:
                    self.driver.add_cookie(cook)
                self.driver.get(url_comment)
                break
            except:
                res = None
                continue
        if res is None:
            self.driver.close()
            return None
        time.sleep(3)
        return self.driver

    def show_more_text(self):
        list_button_more = self.driver.find_elements(By.CLASS_NAME,
                                                     value=self.clas_facebook.list_button_more_text.replace(
                                                         " ", "."))
        while len(list_button_more):
            for each in list_button_more:
                try:
                    if each.get_attribute("role") == "button":
                        if re.search(r"Xem thêm|See more", each.text) is None:
                            continue
                        each.click()
                except:
                    pass
            number_button_more_old = len(list_button_more)
            list_button_more = self.driver.find_elements(By.CLASS_NAME,
                                                         value=self.clas_facebook.list_button_more_text.replace(
                                                             " ", "."))
            if number_button_more_old == len(list_button_more):
                break

    def show_all_comments(self):
        box_comment = self.driver.find_element(By.CLASS_NAME,
                                               value=self.clas_facebook.box_total_comment.replace(" ", "."))

        box_type_comment = box_comment.find_element(By.CLASS_NAME,
                                                    value=self.clas_facebook.box_type_comment.replace(" ", "."))
        next_element = box_type_comment.find_element(By.XPATH, value="./following-sibling::ul")

        child_element = next_element.find_element(By.TAG_NAME, "li")

        list_button_more = child_element.find_elements(By.CLASS_NAME,
                                                       value=self.clas_facebook.list_button_more.replace(" ", "."))
        time_loop = 0
        while len(list_button_more) > 0:
            for each in list_button_more:
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
                    list_button_more = child_element.find_elements(By.CLASS_NAME,
                                                                   value=self.clas_facebook.list_button_more.replace(
                                                                       " ", "."))
                    # self.scroll(1000)
                except:
                    time.sleep(1)
                    continue
            time_loop += 1
            if time_loop == 5:
                break

    def parse_html(self):
        return BeautifulSoup(self.driver.page_source, "lxml")

    def detect_list_reply_update(self, content_comment):
        soup = self.parse_html()
        list_comment = soup.find_all("div", class_=self.clas_facebook.small_box_main_comment)
        box_comment_select = None
        for each_comment in list_comment:
            comment = self.get_data_for_box_comment(each_comment)
            if content_comment in comment["text"]:
                box_comment_select = each_comment
                print(comment["text"])
                break
            content_comment_new = re.sub(r" +", " ", content_comment)
            if content_comment_new in comment["text"]:
                box_comment_select = each_comment
                print(each_comment.text)
                print("000000000000000000000")
                break
        if box_comment_select is None:
            return
        box_comment_select = box_comment_select.find_parent("li")
        if box_comment_select is None:
            return
        box_list_comment = box_comment_select.find_parent("ul")
        if box_list_comment is None:
            return
        return box_list_comment

    def update_dialogue(self, content_comment):
        box_list_comment = self.detect_list_reply_update(content_comment)
        list_replies = []
        if box_list_comment is not None:
            list_replies = self.get_all_replies(box_list_comment)
        return list_replies

    def get_all_replies(self, box_mini_reply):
        list_mini_reply_tag = box_mini_reply.findAll("li")
        list_mini_reply = []
        for each in list_mini_reply_tag:
            tag_mini_reply = each.find("div",
                                       class_=self.clas_facebook.big_box_main_reply_2)
            if tag_mini_reply is None:
                continue
            tag_mini_reply = tag_mini_reply.find("div", class_=self.clas_facebook.small_box_mini_reply)
            if tag_mini_reply is None:
                continue
            mini_reply = self.get_data_for_box_comment(tag_mini_reply)
            list_mini_reply.append(mini_reply)
        return list_mini_reply

    def get_data_for_box_comment(self, box_comment):
        user_main_comment = box_comment.find("span", class_="xt0psk2")
        text_comment = self.get_text_for_box_comment(box_comment)
        tags = self.get_tags_for_box_comment(box_comment)
        attachment = self.get_attachment_for_box_comment(box_comment)
        link_to_reply = self.get_link_to_reply(box_comment)
        data = {"user": user_main_comment.text, "attachment": attachment, "text": text_comment,
                "tags": tags, "link_to_reply": link_to_reply}
        return data

    def get_tags_for_box_comment(self, box_text_comment):
        tags = []
        text_main_comment_box = box_text_comment.find("div", class_=self.clas_facebook.text_main_comment_box_1)
        if text_main_comment_box is None:
            text_main_comment_box = box_text_comment.find("div", class_=self.clas_facebook.text_main_comment_box_2)
        if text_main_comment_box is None:
            return tags
        tags_element = box_text_comment.findAll("a",
                                                class_=self.clas_facebook.tag_elements)
        for tag in tags_element:
            tags.append(tag.text)
        return tags

    def get_attachment_for_box_comment(self, box_comment):
        box_attachment = box_comment.findChild("div", class_=self.clas_facebook.box_attachment, recursive=False)
        data_image = None
        data_link = None
        if box_attachment is None:
            return {"image": data_image, "link": data_link}
        box_image_attachment = box_attachment.find("a",
                                                   class_=self.clas_facebook.box_image_attachment)
        box_link_attachment = box_attachment.find("a",
                                                  class_=self.clas_facebook.box_link_attachment)
        if box_image_attachment is not None:
            image_element = box_image_attachment.find("img")
            if image_element is not None:
                image_source = image_element["src"]
                image_description = image_element["alt"]
                data_image = {"source": image_source, "description": image_description}

        if box_link_attachment is not None:
            link_element = box_link_attachment.find("span")
            if link_element is not None:
                link = box_link_attachment["href"]
                link_description = link_element.text
                data_link = {"source": link, "description": link_description}
        return {"image": data_image, "link": data_link}

    def get_link_to_reply(self, box_comment):
        box_link = box_comment.find("a",
                                    class_=self.clas_facebook.box_link)
        if box_link is None:
            return None
        link_to_reply = box_link.get("href")
        return link_to_reply

    # @staticmethod
    # def process_link_reply(link_reply):
    #     print("ZZZZZZZZZZZZZ")
    #     regex_result = re.search(r"\?comment_id=[\d]+\&reply_comment_id=[\d]+", link_reply)
    #     if regex_result is not None:
    #         start, end = regex_result.span()
    #         return link_reply[:end]
    #     return link_reply

    def get_text_for_box_comment(self, box_text_comment):
        text_main_comment_box = box_text_comment.find("div", class_=self.clas_facebook.text_main_comment_box_1)
        text_comment = ""
        if text_main_comment_box is None:
            text_main_comment_box = box_text_comment.find("div", class_=self.clas_facebook.text_main_comment_box_2)
        if text_main_comment_box is None:
            return None
        list_paragraph_element = text_main_comment_box.findAll("div", attrs={"style": "text-align: start;"})
        for each in list_paragraph_element:
            text_comment += each.get_text(strip=False).strip() + "\n"
        return text_comment.strip()

    def test(self):
        try:
            self.driver = self.access_url_comment(self.url_dialogue)
            self.show_all_comments()
            self.show_more_text()
            dialogue = self.update_dialogue(self.main_reply)
            self.driver.close()
            return dialogue
        except:
            self.driver.close()
            return "Error"
            pass


if __name__ =="__main__":
    dialogue =GetDialogue("https://www.facebook.com/groups/Grouptinhte/posts/4228112633979316/?comment_id=4235699219887324&reply_comment_id=4237784999678746","Nguyễn Phong miễn phí vẫn phải có người giữ chứ bạn? Nếu để tự giữ nếu cvien nhỏ ít người thì dc, cvien đông 1 chút là loạn á, dễ có trộm xe,...")
    print(dialogue.test())