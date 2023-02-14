import re
import time

import requests
import json

from object.replies import GetDialogue
from database.facebook_db import AccountFacebookCollection
from database.facebook_db import DialogueCollection
from database.facebook_db import MainCommentFaceBookCollection
from config.config import Config


class UpdateDialogue:

    def __init__(self):
        self.account_fb_col = AccountFacebookCollection()
        self.dialogue_col = DialogueCollection()
        self.main_comment_col = MainCommentFaceBookCollection()
        self.config = Config()

    @staticmethod
    def get_data_comments_from_graph_api(comment_id, account):
        url = f"https://graph.facebook.com/v15.0/{comment_id}/comments?" \
              f"""access_token={account["token_access"]}"""
        requestJar = requests.cookies.RequestsCookieJar()
        for each in account["cookies"]:
            requestJar.set(each["name"], each["value"])
        try:
            response = requests.get(url, cookies=requestJar)
            jsonformat = json.loads(response.text)
            return jsonformat
        except:
            return None

    def get_last_comment_for_main_comment_graph_api(self, main_comment_id):
        account = self.account_fb_col.get_random_account_active()
        data_graph_api = self. get_data_comments_from_graph_api(main_comment_id, account)
        if data_graph_api is None:
            return
        data_graph_api_before = data_graph_api
        while True:
            try:
                next_page = data_graph_api_before["paging"]["next"]
            except:
                data_graph_api_last = data_graph_api_before
                break
            requestJar = requests.cookies.RequestsCookieJar()
            for each in account["cookies"]:
                requestJar.set(each["name"], each["value"])
            jsonformat = None
            for i in range(5):
                try:
                    response = requests.get(next_page, cookies=requestJar)
                    jsonformat = json.loads(response.text)
                except:
                    continue
            if not len(jsonformat["data"]):
                data_graph_api_last = data_graph_api_before
                break
            data_graph_api_before = jsonformat
        try:
            if data_graph_api_last["error"]["code"] == 100:
                return "COMMENT DELETE"
        except:
            pass

        try:
            if not len(data_graph_api_last["data"]):
                return "COMMENT DELETE"

            # print(data_graph_api_last)
            return data_graph_api_last["data"][-1]
        except:
            pass

    def check_last_main_comment(self, main_comment_id, data_graph_api):
        data_database = self.main_comment_col.query_comment(main_comment_id)
        if not data_database:
            return False
        print("+++++++")
        print(data_database["last_comment"]["message"])
        print(data_graph_api["message"])
        if data_database["last_comment"]["message"] == data_graph_api["message"]:
            return True
        return False

    def get_all_dialogue_of_main_comment(self, main_comment_id):
        list_dialogue = self.dialogue_col.query_all_dialogue_of_main_comment(main_comment_id)
        return list_dialogue

    def merge_text_dialogue(self, dialogue):
        total_text = ""
        for comment in dialogue:
            total_text = total_text + str(comment["text"])
        # print(total_text)
        return self.process_text_before_compare(total_text)

    @staticmethod
    def process_text_before_compare(text):
        return re.sub(r"\s+", " ", text)

    def remove_all_dialogue_of_list_comment(self, comment_id):
        list_dialogue_remove = self.dialogue_col.query_all_dialogue_of_main_comment(comment_id)
        print(list_dialogue_remove)
        for each_dialogue in list_dialogue_remove:
            self.dialogue_col.delete_dialogue(each_dialogue["_id"])
            print(f"DELETE DIALOGUE {each_dialogue}")

    @staticmethod
    def process_time_updated(string_time):
        regex_result = re.search(r"\+\d+", string_time)
        if regex_result is not None:
            start, end = regex_result.span()
            string_time = string_time[:start]
            return string_time
        return string_time

    def check_time_main_comment_update(self, time_facebook, time_dialogue_update_in_database):
        time_facebook = self.process_time_updated(time_facebook)
        time_dialogue_update_in_database = self.process_time_updated(time_dialogue_update_in_database)
        time_facebook_tick = time.mktime(time.strptime(time_facebook, r"%Y-%m-%dT%H:%M:%S")) + 25200
        time_dialogue_update_in_database_tick = time.mktime(time.strptime(time_dialogue_update_in_database, r"%Y-%m-%dT%H:%M:%S")) + 25200

        if time.time() - time_facebook_tick < self.config.interval_to_get_post:
            print(f"MAIN COMMENT TIME {time.time() - time_facebook_tick}")
            return True
        print(f"MAIN COMMENT TIME {time.time() - time_facebook_tick}")
        print("COMMENT TOO OLD")
        return False

    def check_time_main_comment_update(self, time_facebook):
        time_facebook = self.process_time_updated(time_facebook)
        time_facebook_tick = time.mktime(time.strptime(time_facebook, r"%Y-%m-%dT%H:%M:%S")) + 25200
        interval = (time.time() - time_facebook_tick)
        days = interval // 86400
        hour = interval % 86400 // 3600
        minute = interval % 86400 % 3600 // 60
        if interval < self.config.interval_to_get_comment:
            print(f"TIME EXISTED {days} days {hour}hours {minute} minute")
            return True
        print(f"TIME EXISTED {days} days {hour}hours {minute} minute")
        return False

    def update_all_dialogue_waiting_response(self):
        distinct_comment_id = self.dialogue_col.query_all_dialogue_follow_status("waiting response").\
            distinct("comment_id")
        for main_comment_id in distinct_comment_id:
            print("_____________________________________________________________________")
            data_last_comment_graph_api = self.get_last_comment_for_main_comment_graph_api(main_comment_id)
            if data_last_comment_graph_api == "COMMENT DELETE":
                print("MAIN COMMENT CAN BE DELETE")
                self.remove_all_dialogue_of_list_comment(main_comment_id)
                continue
            print(f"MAIN COMMENT ID : {main_comment_id}")
            list_dialogue_for_main_comment = list(self.dialogue_col.query_all_dialogue_waiting_response(main_comment_id))
            if not (self.check_time_main_comment_update(data_last_comment_graph_api["created_time"])):
                for each_dialogue in list_dialogue_for_main_comment:
                    self.dialogue_col.update_status_dialogue(each_dialogue["_id"], "too long response")
                continue
            print(F"DIALOGUE OF COMMENT {main_comment_id} CAN BE UPDATED")
            if self.check_last_main_comment(main_comment_id, data_last_comment_graph_api):
                print(f"NO UPDATE FOR MAIN COMMENT {main_comment_id}")
                continue

            for each_dialogue in list_dialogue_for_main_comment:
                try:
                    link_to_reply = each_dialogue["replies"]["replies"][0]["link_to_reply"]
                    text = each_dialogue["replies"]["replies"][0]["text"]
                except:
                    continue
                # CREATE DIALOGUE (USE SELENIUM TO CRAWL DATA DIALOGUE)
                dialogue = GetDialogue(link_to_reply, text)
                replies_new = dialogue.test()
                if not len(replies_new):
                    break
                if replies_new == "Error":
                    print("Error when get replies")
                    continue
                # CHECK SIMILAR OF DIALOGUE FROM DATABASE AND DIALOGUE FROM CRAWL DATA
                if self.merge_text_dialogue(each_dialogue["replies"]["replies"]) == self.merge_text_dialogue(
                        replies_new):
                    print("----------MATCH----------")
                    # CHECK TIME UPDATE < 2 WEEKS
                    if not (self.check_time_main_comment_update(each_dialogue["updated_time_dialogue"])):
                        self.dialogue_col.update_status_dialogue(each_dialogue["_id"], "too long response")
                else:
                    replies_update = each_dialogue["replies"].copy()
                    replies_update["replies"] = replies_new
                    self.dialogue_col.update_replies_for_dialogue(each_dialogue["_id"], replies_update,
                                                                  data_last_comment_graph_api["created_time"],
                                                                  "response")
                    if replies_new[-1]["text"] == data_last_comment_graph_api["message"]:
                        self.main_comment_col.update_data_main_comment_field_last_comment(main_comment_id,
                                                                                          data_last_comment_graph_api)
                    print(self.dialogue_col.query_dialogue(each_dialogue["_id"]))
            self.update_last_main_comment(main_comment_id, data_last_comment_graph_api)

    def update_all_dialogue_in_database(self):
        # GET DISTINCT MAIN COMMENT ID
        distinct_comment_id = self.dialogue_col.query_distinct_main_comment()
        for main_comment_id in distinct_comment_id:
            print("_____________________________________________________________________")
            # CHECK UPDATE MAIN COMMENT
            data_last_comment_graph_api = self.get_last_comment_for_main_comment_graph_api(main_comment_id)
            if data_last_comment_graph_api == "COMMENT DELETE":
                print("MAIN COMMENT CAN BE DELETE")
                self.remove_all_dialogue_of_list_comment(main_comment_id)
                continue
            print(main_comment_id)
            list_dialogue_for_main_comment = self.get_all_dialogue_of_main_comment(main_comment_id)
            # CHECK TIME UPDATE < 2 WEEKS
            print(data_last_comment_graph_api)
            if not (self.check_time_main_comment_update(data_last_comment_graph_api["created_time"])):
                print(f"SET ALL DIALOGUE OF COMMENT {main_comment_id} NOT TOO LONG RESPONSE")
                for each_dialogue in list_dialogue_for_main_comment:
                    self.dialogue_col.update_status_dialogue(each_dialogue["_id"], "too long response")
                continue
            print(F"DIALOGUE OF COMMENT {main_comment_id} CAN BE UPDATED")
            print(f" NUMBER DIALOGUE IN DATABASE :{len(list_dialogue_for_main_comment)}")

            if self.check_last_main_comment(main_comment_id, data_last_comment_graph_api):
                print(f"NO UPDATE FOR MAIN COMMENT {main_comment_id}")
                continue

            # CHECK UPDATE FOR EVERY DIALOGUE
            for each_dialogue in list_dialogue_for_main_comment:
                try:
                    link_to_reply = each_dialogue["replies"]["replies"][0]["link_to_reply"]
                    text = each_dialogue["replies"]["replies"][0]["text"]
                except:
                    continue
                # CREATE DIALOGUE (USE SELENIUM TO CRAWL DATA DIALOGUE)
                dialogue = GetDialogue(link_to_reply, text)
                replies_new = dialogue.test()
                if not len(replies_new):
                    break
                if replies_new == "Error":
                    print("Error when get replies")
                    continue
                # CHECK SIMILAR OF DIALOGUE FROM DATABASE AND DIALOGUE FROM CRAWL DATA
                if self.merge_text_dialogue(each_dialogue["replies"]["replies"]) == \
                        self.merge_text_dialogue(replies_new):
                    # CHECK TIME UPDATE < 2 WEEKS
                    if not (self.check_time_main_comment_update(each_dialogue["updated_time_dialogue"])):
                        self.dialogue_col.update_status_dialogue(each_dialogue["_id"], "too long response")
                else:
                    replies_update = each_dialogue["replies"].copy()
                    replies_update["replies"] = replies_new
                    if each_dialogue["account_comment"] is not None:
                        self.dialogue_col.update_replies_for_dialogue(each_dialogue["_id"], replies_update,
                                                                      data_last_comment_graph_api["created_time"],
                                                                      "response")
                    else:
                        self.dialogue_col.update_replies_for_dialogue(each_dialogue["_id"], replies_update,
                                                                      data_last_comment_graph_api["created_time"])
                    if self.process_text_before_compare(replies_new[-1]["text"]) == \
                            self.process_text_before_compare(data_last_comment_graph_api["message"]):
                        self.main_comment_col.update_data_main_comment_field_last_comment(main_comment_id,
                                                                                          data_last_comment_graph_api)
                    print(self.dialogue_col.query_dialogue(each_dialogue["_id"]))
            self.update_last_main_comment(main_comment_id, data_last_comment_graph_api)

    def update_last_main_comment(self, main_comment_id,data_last_comment_graph_api):
        self.main_comment_col.update_data_main_comment_field_last_comment(main_comment_id, data_last_comment_graph_api)

    # REMOVE DIALOGUE TOO LONG RESPONSE
    def remove_dialogue_too_long_response(self):
        list_dialogue = self.dialogue_col.query_all_dialogue_follow_status("too long response")
        for dialogue in list_dialogue:
            self.dialogue_col.delete_dialogue(dialogue["_id"])
            print(f"""REMOVE DIALOGUE {dialogue["_id"]}""")


if __name__ == "__main__":

    update = UpdateDialogue()
    update.remove_dialogue_too_long_response()
    update.update_all_dialogue_waiting_response()
    while True:
        # update.update_all_dialogue_in_database()
        # update.remove_dialogue_too_long_response()
        update.update_all_dialogue_waiting_response()
        time.sleep(60*10)
