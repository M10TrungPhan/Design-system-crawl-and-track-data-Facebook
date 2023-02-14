from database.facebook_db import FacebookCollection
import os
import json

fb_db = FacebookCollection()

dir_folder = "//172.29.13.24/tmtaishare/Data/facebook/"
for page in os.listdir(dir_folder):
    dir_data = dir_folder + page + "/"
    print(dir_data)
    for file in os.listdir(dir_data):
        name_file = dir_data + file
        data = json.load(open(name_file, "r", encoding="utf-8"))
        # print(name_file)
        if "name_page" not in data.keys():
            data["name_page"] = page
        data["_id"] = data["id_post"]
        del data["id_post"]
        fb_db.save_data(data)
        # print(data)
