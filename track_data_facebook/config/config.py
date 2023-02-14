from object.singleton import Singleton
import os
from common.common_keys import *


class Config(metaclass=Singleton):
    path_save_data = os.getenv(PATH_SAVE_DATA, "//172.29.13.24/tmtaishare/Data/Data_GROUP_FACEBOOK_2/")
    number_of_crawler = os.getenv(NUMBER_OF_CRAWLER, 2)
    logging_folder = "log/"
    mongodb_host = os.getenv(MONGODB_HOST, '172.29.13.23')
    mongodb_port = int(os.getenv(MONGODB_PORT, '20253'))
    mongodb_username = os.getenv(MONGODB_USERNAME, 'admin')
    mongodb_password = os.getenv(MONGODB_PASSWORD, 'admin')
    fb_database = os.getenv(FB_DATABASE, "facebook")
    data_fb_collection = os.getenv(DATA_FB_COLLECTION, "fb_data")
    account_fb_collection = os.getenv(ACCOUNT_FB_COLLECTION, "account_fb")
    time_update_post_collection = os.getenv(TIME_UPDATE_POST_COLLECTION, "time_update_post")
    dialogue_collection = os.getenv(DIALOGUE_COL, "dialogue_col")
    main_comment_fb = os.getenv(MAIN_COMMENT_FB, "main_comment_fb")
    list_fanpage_collection = os.getenv(LIST_FANPAGE_COLLECTION, 'list_fanpage')
    interval_to_get_post = 1209600
    interval_to_get_comment = 1209600

