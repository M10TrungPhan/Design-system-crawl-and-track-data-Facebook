from database.facebook_db import TimePostUpdateCollection
import os
import json

database_update_time = TimePostUpdateCollection()
folder_data = r"\\172.29.13.24\tmtaishare\Data\Data_GROUP_FACEBOOK_2\\"
list_group = os.listdir(folder_data)
for each_group in list_group:
    folder_group = folder_data + each_group + "\\"
    list_file = os.listdir(folder_group)
    for each_file in list_file:
        name_file = folder_group + each_file
        data = json.load(open(name_file, "r", encoding="utf-8"))
        if "updated_time" not in data.keys():
            continue
        post_new = {"_id": data["_id"], "updated_time": data["update_time"]}
        if database_update_time.check_update_time(post_new):
            print("XXXXXXXXX")
            continue
        database_update_time.save_update_time_for_post(post_new )

