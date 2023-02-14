import time
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import re
import pymongo
import random
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup


class AutoCommentService:
    def __init__(self):
        self.driver = None

    @staticmethod
    def setup_selenium_firefox():
        ser = Service("driverbrower/geckodriver.exe")
        firefox_options = FirefoxOptions()
        firefox_options.set_preference("media.volume_scale", "0.0")
        firefox_options.set_preference('devtools.jsonview.enabled', False)
        firefox_options.set_preference('dom.webnotifications.enabled', False)
        firefox_options.add_argument("--test-type")
        firefox_options.add_argument('--ignore-certificate-errors')
        firefox_options.add_argument('--disable-extensions')
        firefox_options.add_argument('disable-infobars')
        firefox_options.add_argument("--incognito")
        # firefox_options.add_argument("--headless")
        driver = webdriver.Firefox(service=ser, options=firefox_options)
        return driver

    @staticmethod
    def get_random_account_active():
        client = pymongo.MongoClient(host="172.29.13.23", port=20253, username="admin", password="admin")
        database = client["facebook"]
        facebook_col = database["account_fb"]
        myquery = {"status": "active", "user":"harkdead1@proton.me"}
        list_account = []
        for x in facebook_col.find(myquery):
            list_account.append(x)
        return list_account[random.randint(0, len(list_account) - 1)]
    @staticmethod
    def process_link_reply(link_reply):
        regex_result = re.search(r"\?comment_id=[\d]+&reply_comment_id=[\d]+", link_reply)
        if regex_result is not None:
            start, end = regex_result.span()
            return link_reply[:end]
        return link_reply

    @staticmethod
    def process_link_comment(link_comment):
        regex_result = re.search(r"\?comment_id=\d+", link_comment)
        if regex_result is not None:
            start, end = regex_result.span()
            return link_comment[:end]
        return link_comment

    def access_url_comment(self, url_comment):
        account = self.get_random_account_active()
        self.driver = self.setup_selenium_firefox()
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
                                                value="x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xt0b8zv xzsf02u x1s688f".replace(
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
                                                    value="x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xt0b8zv xzsf02u x1s688f".replace(
                                                        " ", "."))
            if number_button_more_old == len(list_button_more):
                break

    def show_all_comments(self):
        box_comment = self.driver.find_element(By.CLASS_NAME, value="x1jx94hy x12nagc".replace(" ", "."))

        element_comment = box_comment.find_element(By.CLASS_NAME, value="x1iorvi4 x1pi30zi xjkvuk6 x1swvt13".
                                                   replace(" ", "."))
        next_element = element_comment.find_element(By.XPATH, value="./following-sibling::ul")

        child_element = next_element.find_element(By.TAG_NAME, "li")

        list_button_more = child_element.find_elements(By.CLASS_NAME,
                                                     value="x78zum5 x1w0mnb xeuugli".replace(" ", "."))
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
                                                         value="x78zum5 x1w0mnb xeuugli".replace(
                                                             " ", "."))
                    # self.scroll(1000)
                except:
                    time.sleep(1)
                    continue
            time_loop += 1
            if time_loop == 5:
                break

    def detect_box_comment_to_reply(self, content_comment):
        list_comment = self.driver.find_elements(By.CLASS_NAME,
                                            value="x1r8uery x1iyjqo2 x6ikm8r x10wlt62 x1pi30zi".replace(" ", "."))
        for each in list_comment:
            if content_comment in each.text:
                box_comment_select = each
                break
            content_comment_new = re.sub(r" +", " ", content_comment)
            if content_comment_new in each.text:
                box_comment_select = each
                break
        return box_comment_select

    @staticmethod
    def click_reply_button(comment_select):
        list_button = comment_select.find_elements(By.CLASS_NAME,
                                                   value="x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x9f619 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xi81zsa x1ypdohk x1rg5ohu x117nqv4 x1n2onr6 xt0b8zv".replace(
                                                       " ", "."))
        for each in list_button:
            if re.search(r"Phản hồi|Reply", each.text, flags=re.IGNORECASE) is not None:
                button_select = each
        button_select.click()

    def detect_box_reply(self, user_comment):
        list_box_reply = self.driver.find_elements(By.CLASS_NAME,
                                              value="xzsf02u x1a2a7pz x1n2onr6 x14wi4xw notranslate".replace(" ", "."))
        for each in list_box_reply:
            if user_comment in each.text:
                reply_box_select = each
        return reply_box_select

    @staticmethod
    def send_reply_comment(box_reply, content_reply):
        for each in content_reply:
            box_reply.send_keys(each)
        time.sleep(5)
        box_reply.send_keys(Keys.ENTER)
        box_reply.send_keys(Keys.ENTER)

    def parse_html(self):
        return BeautifulSoup(self.driver.page_source, "lxml")

    def detect_list_reply_update(self, content_comment):
        soup = self.parse_html()
        list_comment = soup.find_all("div", class_="x1r8uery x1iyjqo2 x6ikm8r x10wlt62 x1pi30zi")
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
                                       class_="x1n2onr6 x1iorvi4 x4uap5 x18d9i69 xurb0ha x78zum5 x1q0g3np x1a2a7pz")
            if tag_mini_reply is None:
                continue
            tag_mini_reply = tag_mini_reply.find("div", class_="x1r8uery x1iyjqo2 x6ikm8r x10wlt62 x1pi30zi")
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
        link_to_reply = self.process_link_reply(self.get_link_to_reply(box_comment))
        data = {"user": user_main_comment.text, "attachment": attachment, "text": text_comment,
                "tags": tags, "link_to_reply": link_to_reply}
        return data

    @staticmethod
    def get_tags_for_box_comment(box_text_comment):
        tags = []
        text_main_comment_box = box_text_comment.find("div", class_="xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs")
        if text_main_comment_box is None:
            text_main_comment_box = box_text_comment.find("div", class_="x11i5rnm xat24cr x1mh8g0r x1vvkbs xdj266r")
        if text_main_comment_box is None:
            return tags
        tags_element = box_text_comment.findAll("a",
                                                class_="x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xt0b8zv xzsf02u x1s688f")
        for tag in tags_element:
            tags.append(tag.text)
        return tags

    @staticmethod
    def get_attachment_for_box_comment(box_comment):
        box_attachment = box_comment.findChild("div", class_="x78zum5 xv55zj0 x1vvkbs", recursive=False)
        data_image = None
        data_link = None
        if box_attachment is None:
            return {"image": data_image, "link": data_link}
        box_image_attachment = box_attachment.find("a",
                                                   class_="x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz")
        box_link_attachment = box_attachment.find("a",
                                                  class_="x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1ey2m1c xds687c x10l6tqk x17qophe x13vifvy xi2jdih")
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

    @staticmethod
    def get_link_to_reply(box_comment):
        box_link = box_comment.find("a", class_="x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xt0b8zv xi81zsa x1fcty0u")
        if box_link is None:
            return None
        link_to_reply = box_link.get("href")
        # print(link_to_reply)
        return link_to_reply

    @staticmethod
    def get_text_for_box_comment(box_text_comment):
        text_main_comment_box = box_text_comment.find("div", class_="xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs")
        text_comment = ""
        if text_main_comment_box is None:
            text_main_comment_box = box_text_comment.find("div", class_="x11i5rnm xat24cr x1mh8g0r x1vvkbs xdj266r")
        if text_main_comment_box is None:
            return None
        list_paragraph_element = text_main_comment_box.findAll("div", attrs={"style": "text-align: start;"})
        for each in list_paragraph_element:
            text_comment += each.get_text(strip=False).strip() + "\n"
        return text_comment.strip()

    def auto_post_comment(self, user_comment, url_comment, content_comment, content_reply):
        self.driver = self.access_url_comment(url_comment)
        try:
            self.show_all_comments()
            print(1)
            self.show_more_text()
            print(2)

            box_comment_select = self.detect_box_comment_to_reply(content_comment)
            print(3)
            self.click_reply_button(box_comment_select)
            print(4)
            box_send_reply = self.detect_box_reply(user_comment)
            print(5)
            self.send_reply_comment(box_send_reply, content_reply)
            time.sleep(10)
            print(self.update_dialogue(content_comment))
            # self.driver.close()
        except:
            # self.driver.close()
            pass


auto_post_comment_tool = AutoCommentService()
user_comment = "Thanh Hà Kiều"
url_comment = "https://www.facebook.com/groups/khoahocxgr/posts/5776094522437012/?comment_id=5776414439071687&reply_comment_id=5778644902181974&notif_id=1670234661672541&notif_t=group_comment_mention"
content_comment = "Hải Trần chứ bạn có ý kiến gì comment của mình k =)))"
content_reply = "mình không hiểu gì hết"
auto_post_comment_tool.auto_post_comment(user_comment, url_comment, content_comment, content_reply)

