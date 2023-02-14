from service.manage_account_facebook import ManageAccountFacebook
from service.update_dialogue import UpdateDialogue
from service.generate_dialogue_service import GenerateDialogue

import time


if __name__ == "__main__":
    mn = ManageAccountFacebook()
    mn.update_information_for_all_account_to_comment()

    # GENERATE DIALOGUE
    path_save_data = r"\\172.29.13.24\tmtaishare\Data\Data_GROUP_FACEBOOK_2\Cộng Đồng Chia Sẻ - Nâng Tầm Kiến Thức (XGR)\\"
    generate_service = GenerateDialogue(path_save_data)
    # generate_service.generate_dialogue_from_path_folder()
    #
    # UPDATE DIALOGUE
    update = UpdateDialogue()
    update.remove_dialogue_too_long_response()
    while True:
        update.update_all_dialogue_in_database()
        update.remove_dialogue_too_long_response()
        update.update_all_dialogue_waiting_response()
        time.sleep(60*30)
