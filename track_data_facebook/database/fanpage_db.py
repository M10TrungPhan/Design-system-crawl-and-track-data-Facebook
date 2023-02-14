from database.mongo_client import MongoDatabase
from config.config import Config


class FanpageDB:
    def __init__(self):
        self.config = Config()
        self.mongodb = MongoDatabase()
        self.database = self.mongodb.client[self.config.fb_database]
        self.data_col = self.database[self.config.list_fanpage_collection]
    
    def add_page(self, data):
        self.data_col.insert_one(data)

    def remove_page(self, data):
        self.data_col.delete_one(data)

    def get_all_list_fanpage(self):
        list_fanpage = []
        for x in self.data_col.find():
            list_fanpage.append(x)
        return list_fanpage
    
    def get_info_by_id(self, page_id):
        query = {'_id': page_id}
        for x in self.data_col.find(query):
            page = x
        if page is None:
            return
        return page
    
    def get_list_pages_by_status(self, status):
        list_pages = []
        for x in self.data_col.find({'status':status}):
            list_pages.append(x)
        return list_pages