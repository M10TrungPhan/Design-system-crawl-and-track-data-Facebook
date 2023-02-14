import random
import hashlib
from threading import Lock

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
        self.lock_func_get_account = Lock()

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

    def query_account_follow_username(self, username):
        account = None
        query_condition = {"user": username}
        for x in self.data_col.find(query_condition):
            account = x
        if account is None:
            return
        return account

    def update_status_account(self, username, status):
        query_condition = {"user": username}
        new_values = {"$set": { "status": status}}
        self.data_col.update_one(query_condition, new_values)
        return f"UPDATE SUCCESSFUL FOR USER {username}"

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
            if x["status"] == "comment":
                continue
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

    def get_account_to_crawl(self):
        try:
            query_condition = {"status": "active"}
            list_account = []
            self.lock_func_get_account.acquire()
            for x in self.data_col.find(query_condition):
                list_account.append(x)
            if not len(list_account):
                self.lock_func_get_account.release()
                return None
            account_select = list_account[random.randint(0, len(list_account)-1)]
            self.update_status_account(account_select["user"], "in use")
            self.lock_func_get_account.release()
            print(f"""GET ACCOUNT {account_select["user"]} CRAWL """)
            # print()
            return account_select
        except Exception as e:
            print(f"ERROR FUNC  GET ACCOUNT TO CRAWL: {e}")
            return None


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




