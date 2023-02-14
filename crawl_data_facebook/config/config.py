from object.singleton import Singleton
import os
from common.common_keys import *


class Config(metaclass=Singleton):
    path_save_data = os.getenv(PATH_SAVE_DATA, r"\\smb-ai.tmt.local/Public-AI/Public/Data/Data_GROUP_FACEBOOK_2/")
    number_of_crawler = os.getenv(NUMBER_OF_CRAWLER, 4)
    number_of_crawler_video = os.getenv(NUMBER_OF_CRAWLER, 2)
    number_video_crawl = os.getenv(NUMBER_OF_CRAWLER, 50)
    logging_folder = "log/"
    mongodb_host = os.getenv(MONGODB_HOST, '172.29.13.23')
    mongodb_port = int(os.getenv(MONGODB_PORT, '20253'))

    mongodb_username = os.getenv(MONGODB_USERNAME, 'admin')
    mongodb_password = os.getenv(MONGODB_PASSWORD, 'admin')
    fb_database = os.getenv(FB_DATABASE, "facebook")
    data_fb_collection = os.getenv(DATA_FB_COLLECTION, "fb_data")
    account_fb_collection = os.getenv(ACCOUNT_FB_COLLECTION, "account_fb")
    time_for_load_comment = 15
    time_update_post_collection = os.getenv(TIME_UPDATE_POST_COLLECTION, "time_update_post")
    list_fanpage_collection = os.getenv(LIST_FANPAGE_COLLECTION, 'list_fanpage')
    interval_to_get_post = 1814400

