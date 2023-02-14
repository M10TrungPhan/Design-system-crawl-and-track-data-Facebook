from database.facebook_db import TimePostUpdateCollection
import os
import json

database_update_time = TimePostUpdateCollection()
folder_data = r"\\172.29.13.24\tmtaishare\Data\Data_GROUP_FACEBOOK_2\unknown\\"
list_group = os.listdir(folder_data)
for each_group in list_group:
    folder_group = folder_data + each_group + "\\"
    list_file = os.listdir(folder_group)
    for each_file in list_file:
        name_file = each_file.replace(".json", "")
        print(name_file)
        my_query = {"_id": name_file}
        database_update_time.data_col.delete_one(my_query)

