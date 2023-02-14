import random
import hashlib

from object.account_fb_request import AccountFacebookRequest
from database.mongo_client import MongoDatabase
from config.config import Config
from object.singleton import Singleton


class FacebookCollection(metaclass=Singleton):
    def __init__(self):
        self.config = Config()
        self.mongodb = MongoDatabase()
        self.database = self.mongodb.client[self.config.fb_database]
        self.data_col = self.database[self.config.data_fb_collection]

    def save_data(self, data):
        self.data_col.insert_one(data)

    def get_list_id_for_page(self, name_page):
        name_page_query = {"name_page": name_page}
        list_id_post = []
        for each in self.data_col.find(name_page_query):
            list_id_post.append(each["_id"])
        return list_id_post


class AccountFacebookCollection(metaclass=Singleton):
    def __init__(self):
        self.config = Config()
        self.mongodb = MongoDatabase()
        self.database = self.mongodb.client[self.config.fb_database]
        self.data_col = self.database[self.config.account_fb_collection]

    def create_account(self, data):
        self.data_col.insert_one(data)

    def remove_account(self, data):
        self.data_col.delete_one(data)

    def random_account(self):
        list_account = []
        for x in self.data_col.find():
            list_account.append(x)
        if not len(list_account):
            return None
        return list_account[0]

    def query_account_follow_id(self, account_id):
        account = None
        query_condition = {"_id": account_id}
        for x in self.data_col.find(query_condition):
            account = x
        if account is None:
            return
        return account

    def query_account_follow_username(self, user_name):
        account = None
        query_condition = {"user": user_name}
        for x in self.data_col.find(query_condition):
            account = x
        if account is None:
            return
        return account

    def update_information_account_api(self, account: AccountFacebookRequest):
        id_user = hashlib.md5(account.username.encode("utf-8")).hexdigest()
        account_in_db = self.query_account_follow_id(id_user)
        if account_in_db is None:
            return f"User not existed"
        old_password = account_in_db["password"]
        old_status = account_in_db["status"]
        old_token_access = account_in_db["token_access"]
        old_cookies = account_in_db["cookies"]
        old_account_name = account_in_db["account_name"]
        if account.password is None:
            update_password = old_password
        else:
            update_password = account.password
        if account.status is None:
            update_status = old_status
        else:
            update_status = account.status
        if account.cookies is None:
            update_cookies = old_cookies
        else:
            update_cookies = account.cookies

        if account.token_access is None:
            update_token_access = old_token_access
        else:
            update_token_access = account.token_access

        if account.account_name is None:
            update_account_name = old_account_name
        else:
            update_account_name = account.account_name

        query_condition = {"_id": id_user}
        new_values = {"$set": {"password": update_password, "status": update_status,
                               "token_access": update_token_access, "cookies": update_cookies,
                               "account_name": update_account_name}}
        self.data_col.update_one(query_condition, new_values)
        return f"UPDATE SUCCESSFUL FOR USER {account.username}"

    def get_information_all_account(self):
        list_account = []
        for x in self.data_col.find():
            list_account.append(x)
        return list_account

    def get_all_account_active(self):
        list_account = []
        query_condition = {"status": "active"}
        for x in self.data_col.find(query_condition):
            list_account.append(x)
        return list_account

    def get_random_account_active(self):
        list_account = self.get_all_account_active()
        # print(list_account[5])
        return list_account[random.randint(0, len(list_account)-1)]
        # return  list_account[5]


class TimePostUpdateCollection(metaclass=Singleton):
    def __init__(self):
        self.config = Config()
        self.mongodb = MongoDatabase()
        self.database = self.mongodb.client[self.config.fb_database]
        self.data_col = self.database[self.config.time_update_post_collection]

    def query_information_for_post(self, post_id):
        query_condition = {"_id": post_id}
        post = None
        for x in self.data_col.find(query_condition):
            post = x
        if post is None:
            return False
        return post

    def save_update_time_for_post(self, data: dict):
        self.data_col.insert_one(data)

    def remove_update_time_for_post(self, data: dict):
        self.data_col.delete_one(data)

    def update_time_for_post(self, data: dict):
        post_id = data["_id"]
        if not self.query_information_for_post(post_id):
            self.save_update_time_for_post(data)
            return
        query_condition = {"_id": post_id}
        new_values = {"$set": {"updated_time": data["updated_time"]}}
        self.data_col.update_one(query_condition, new_values)

    def check_update_time(self, post_new: dict):
        post_id = post_new["_id"]
        post_old = self.query_information_for_post(post_id)
        if not post_old:
            # print("POST NO EXIST")
            return False
        if post_new["updated_time"] == post_old["updated_time"]:
            return True
        return False


class DialogueCollection(metaclass=Singleton):

    def __init__(self):
        self.config = Config()
        self.mongodb = MongoDatabase()
        self.database = self.mongodb.client[self.config.fb_database]
        self.data_col = self.database[self.config.dialogue_collection]

    def insert_new_dialogue(self, data):
        self.data_col.insert_one(data)

    def delete_dialogue(self, dialogue_id):
        self.data_col.delete_one({"_id": dialogue_id})

    def query_dialogue(self, dialogue_id):
        myquery = {"_id": dialogue_id}
        list_result = []
        for each in self.data_col.find(myquery):
            list_result.append(each)
        return list_result

    def query_all_dialogue_of_main_comment(self, comment_id):
        myquery = {"comment_id": comment_id}
        list_dialogue = []
        for item in self.data_col.find(myquery):
            list_dialogue.append(item)
        return list_dialogue

    def query_all_dialogue_follow_status(self, status):
        myquery = {"status_dialogue": status}
        return self.data_col.find(myquery)

    def query_all_dialogue_waiting_response(self, comment_id):
        myquery = {"status_dialogue": "waiting response", "comment_id": comment_id}
        return self.data_col.find(myquery)

    def query_distinct_main_comment(self):
        return self.data_col.distinct("comment_id")

    def update_replies_for_dialogue(self, dialogue_id, replies, *args):
        query_condition = {"_id": dialogue_id}
        set_information_update = {"replies": replies}
        if len(args):
            if args[0] is not None:
                set_information_update["updated_time_dialogue"] = args[0]
        if len(args) > 1:
            set_information_update["status_dialogue"] = args[1]
        if len(args) > 2:
            set_information_update["account_comment"] = args[2]
        new_values = {"$set": set_information_update}
        self.data_col.update_one(query_condition, new_values)
        print(f"UPDATE REPLIES DIALOGUE {dialogue_id} and status to {set_information_update}")

    def update_status_dialogue(self, dialogue_id, status):
        query_condition = {"_id": dialogue_id}
        new_values = {"$set": {"status_dialogue": status}}
        self.data_col.update_one(query_condition, new_values)
        print(f"UPDATE DIALOGUE {dialogue_id} to {status}")

    def update_replies_for_dialogue_response(self, dialogue_id, replies):
        query_condition = {"_id": dialogue_id}
        new_values = {"$set": {"replies": replies, "status_dialogue": "response"}}
        self.data_col.update_one(query_condition, new_values)
        print("UPDATE DIALOGUE RESPONSE")

    def update_dialogue_after_post_comment(self, dialogue_id, replies, account_comment):
        query_condition = {"_id": dialogue_id}
        new_values = {"$set": {"replies": replies, "account_comment": account_comment,
                               "status_dialogue": "waiting response"}}
        self.data_col.update_one(query_condition, new_values)
        print("UPDATE DIALOGUE")


class MainCommentFaceBookCollection(metaclass=Singleton):

    def __init__(self):
        self.config = Config()
        self.mongodb = MongoDatabase()
        self.database = self.mongodb.client[self.config.fb_database]
        self.data_col = self.database[self.config.main_comment_fb]

    def insert_new_data(self, data):
        self.data_col.insert_one(data)

    def query_comment(self, comment_id):
        myquery = {"_id": comment_id}
        result_query = self.data_col.find_one(myquery)
        if result_query is None:
            return False
        return result_query

    def update_data_main_comment_field_last_comment(self, main_comment_id, main_comment_update):
        data_in_database = self.query_comment(main_comment_id)
        if not data_in_database:
            self.data_col.insert_one({"_id":main_comment_id, "last_comment": main_comment_update})
            # print("CREATE NEW MAIN COMMENT DATA")
            return
        last_comment_old = data_in_database["last_comment"]
        if main_comment_update == last_comment_old:
            # print("NOT UPDATE MAIN COMMENT")
            return
        last_comment_update = main_comment_update
        # print(last_comment_update)
        query_condition = {"_id": main_comment_id}
        new_values = {"$set": {"last_comment": last_comment_update}}
        self.data_col.update_one(query_condition, new_values)
        # print("UPDATE MAIN COMMENT")
