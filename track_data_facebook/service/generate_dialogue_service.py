import os
import re
import json
import time

from database.facebook_db import DialogueCollection
from database.facebook_db import MainCommentFaceBookCollection
from service.update_dialogue import UpdateDialogue
from config.config import Config


class GenerateDialogue:

    def __init__(self, path_save_data):
        self.path_save_data = self.process_path_save_data(path_save_data)
        self.dialogue_col = DialogueCollection()
        self.main_comment_dialogue = MainCommentFaceBookCollection()
        self.update_dialogue = UpdateDialogue()
        self.config = Config()

    @staticmethod
    def process_path_save_data(path_save_data):
        if re.search(r"\\$|/$", path_save_data) is None:
            return path_save_data + "/"
        return path_save_data

    # LOAD LIST DATA TO GENERATE DIALOGUE / CAN SET CONDITION FOR POST HAVE TIME RECENTLY CREATED
    def load_data_post_facebook(self):
        list_data = os.listdir(self.path_save_data)
        return [(self.path_save_data + id_post) for id_post in list_data]

    # PROCESS LINK REPLY TO STANDARD
    @staticmethod
    def process_link_reply(link_reply):
        regex_result = re.search(r"\?comment_id=[\d]+&reply_comment_id=[\d]+", link_reply)
        if regex_result is not None:
            start, end = regex_result.span()
            return link_reply[:end]
        return link_reply

    # PROCESS LINK COMMENT TO STANDARD
    @staticmethod
    def process_link_comment(link_comment):
        regex_result = re.search(r"\?comment_id=\d+", link_comment)
        if regex_result is not None:
            start, end = regex_result.span()
            return link_comment[:end]
        return link_comment

    # GET COMMENT ID FROM LINK TO REPLY
    @staticmethod
    def get_comment_id(link_comment):
        regex_result = re.search(r"\?comment_id=\d+", link_comment)
        if regex_result is None:
            return None
        start, end = regex_result.span()
        string_comment_id = link_comment[start:end]
        regex_result_2 = re.search(r"\d+", string_comment_id)
        if regex_result is None:
            return None
        start, end = regex_result_2.span()
        return string_comment_id[start:end]

    # GET REPLY ID FROM LINK TO REPLY
    @staticmethod
    def get_reply_id(link_reply):
        # GET REPLY ID FROM LINK TO REPLY
        regex_result = re.search(r"&reply_comment_id=\d+", link_reply)
        if regex_result is None:
            return None
        start, end = regex_result.span()
        string_reply_id = link_reply[start:end]
        regex_result_2 = re.search(r"\d+", string_reply_id)
        if regex_result is None:
            return None
        start, end = regex_result_2.span()
        return string_reply_id[start:end]

    # SAVE DIALOGUE TO  DIALOGUE COLLECTION
    def save_dialogue(self, data):
        self.dialogue_col.insert_new_dialogue(data)

    # GENERATE DIALOGUE FROM ONE POST
    def generate_dialogue_for_one_post_facebook(self, file, *args):
        try:
            data = json.load(open(file, "r", encoding="utf-8"))
            if "updated_time" not in data.keys():
                return []
            if data["updated_time"] is None:
                return []

            if not self.check_time_post_update(data["updated_time"]):
                return []
            # LOAD DATA FROM FACEBOOK
            post_id = data["_id"]
            list_dialogue = []
            # print(f"""NUMBER MAIN COMMENT: {len(data["comment"])}""")
            # ITERATE EACH MAIN COMMENT
            for main_comment in data["comment"]:
                list_last_reply = []
                main_comment_id = self.get_comment_id(main_comment["link_to_reply"])
                # print("++++++++++")
                # print(f"MAIN_COMMENT_ID: {main_comment_id}")
                # print(f"""NUMBER DIALOGUE COMMENT: {len(main_comment["replies"])}""")
                # ITERATE MAIN REPLY
                if not len(main_comment["replies"]):
                    continue
                data_last_comment_graph_api = self.update_dialogue.get_last_comment_for_main_comment_graph_api(
                    main_comment_id)
                if data_last_comment_graph_api == "COMMENT DELETE":
                    # print("MAIN COMMENT CAN BE DELETE")
                    continue
                if not(self.check_time_main_comment_update(data_last_comment_graph_api["created_time"])):
                    continue
                # print(data_last_comment_graph_api)
                for main_reply in main_comment["replies"]:
                    # print("**********")
                    # print(f"""NUMBER COMMENT IN DIALOGUE: {len(main_reply["replies"])}""")
                    # print(main_reply["text"])
                    list_last_reply.append(main_reply["text"])
                    # GET DIALOGUE > 3 COMMENT
                    if not len(main_reply["replies"]):
                        # print("DIALOGUE < 3 comment")
                        continue
                    main_reply_id = self.get_reply_id(main_reply["link_to_reply"])
                    dialogue_id = str(post_id) + "_" + main_comment_id + "_" + main_reply_id
                    # print(f"DIALOGUE_ID: {dialogue_id}")
                    # CHECK DIALOGUE IN DATABASE / ONLY CREATE DIALOGUE NOT IN DATABASE
                    if len(self.dialogue_col.query_dialogue(dialogue_id)):
                        # print("DIALOGUE EXISTED")
                        continue
                    dialogue_new = main_comment.copy()
                    dialogue_new["content_post"] = data["content"]

                    dialogue_new["updated_time_dialogue"] = data_last_comment_graph_api["created_time"]
                    dialogue_new["status_dialogue"] = "Normal"
                    dialogue_new["comment_id"] = main_comment_id
                    dialogue_new["_id"] = dialogue_id
                    dialogue_new["reply_id"] = main_reply_id
                    main_reply["link_to_reply"] = self.process_link_reply(main_reply["link_to_reply"])
                    dialogue_new["replies"] = main_reply
                    dialogue_new["link_to_reply"] = self.process_link_comment(dialogue_new["link_to_reply"])
                    if not len(args):
                        dialogue_new["account_comment"] = None
                    else:
                        dialogue_new["account_comment"] = args[0]
                    list_last_reply.append(str(main_reply["replies"][-1]["text"]))
                    # CREATE DIALOGUE
                    self.save_dialogue(dialogue_new)
                    print("CREATE DIALOGUE")
                    list_dialogue.append(dialogue_new)
                # CHECK LAST COMMENT IN MAIN COMMENT IF IT ON ANY DIALOGUE
                data_last_comment_graph_api = self.update_dialogue.\
                    get_last_comment_for_main_comment_graph_api(main_comment_id)
                # CHECK MAIN COMMENT CAN BE DELETE => REMOVE ALL DIALOGUE OF ITS MAIN COMMENT
                # if data_last_comment_graph_api == "COMMENT DELETE":
                #     self.remove_all_dialogue_of_list_comment(main_comment_id)
                #     print("COMMENT CAN BE DELETE")
                #     continue

                text_last_comment = data_last_comment_graph_api["message"]
                if text_last_comment in list_last_reply:
                    # UPDATE MAIN COMMENT
                    # print(f"UPDATE MAIN COMMENT {main_comment_id}")
                    self.main_comment_dialogue.update_data_main_comment_field_last_comment(main_comment_id,
                                                                                           data_last_comment_graph_api)
            return list_dialogue
        except:
            return  []

    def remove_all_dialogue_of_list_comment(self, comment_id):
        list_dialogue_remove = self.dialogue_col.query_all_dialogue_of_main_comment(comment_id)
        # print(list_dialogue_remove)
        for each_dialogue in list_dialogue_remove:
            self.dialogue_col.delete_dialogue(each_dialogue["_id"])
            # print(f"DELETE DIALOGUE {each_dialogue}")

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
            print(f"TIME EXISTED {days} days {hour}hours {minute} minute")
            return True
        print(f"TIME EXISTED {days} days {hour}hours {minute} minute")
        print("POST TOO OLD")
        return False

    def check_time_main_comment_update(self, time_facebook):
        time_facebook = self.process_time_updated(time_facebook)
        time_facebook_tick = time.mktime(time.strptime(time_facebook, r"%Y-%m-%dT%H:%M:%S")) + 25200
        interval = (time.time() - time_facebook_tick)
        # print(interval)
        days = interval // 86400
        hour = interval % 86400 // 3600
        minute = interval % 86400 % 3600 // 60
        if int(interval) < self.config.interval_to_get_comment:
            print(f"TIME EXISTED {days} days {hour}hours {minute} minute")
            return True
        print(f"TIME EXISTED {days} days {hour}hours {minute} minute")
        print("COMMENT TOO OLD")
        return False

    # UPDATE DIALOGUE FROM SOURCE DATA ( DATA FACEBOOK COLLECTION)
    def generate_dialogue_from_path_folder(self):
        number_dialogue = 0
        list_post_facebook = self.load_data_post_facebook()
        print(len(list_post_facebook))
        for post in list_post_facebook:
            print("________________________________________________________________________________________")
            list_dialogue = self.generate_dialogue_for_one_post_facebook(post)
            print(f"NUMBER DIALOGUE GENERATE OF POST {post} is {len(list_dialogue)})")
            number_dialogue += len(list_dialogue)
        print(f"TOTAL NUMBER DIALOGUE CREATE {number_dialogue}")


if __name__ == "__main__":
    path_save_data = r"\\172.29.13.24\tmtaishare\Data\Data_GROUP_FACEBOOK_2\Phản Biện Không Thuyết Phục_ Xóa Group! (XGR)/text/"
    generate_service = GenerateDialogue(path_save_data)
    generate_service.generate_dialogue_from_path_folder()



