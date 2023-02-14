import re
import json


def process_link_reply(link_reply):
    regex_result = re.search(r"\?comment_id=[\d]+&reply_comment_id=[\d]+", link_reply)
    if regex_result is not None:
        start,end = regex_result.span()
        return link_reply[:end]
    return link_reply


def process_link_comment(link_comment):
    regex_result = re.search(r"\?comment_id=\d+", link_comment)
    if regex_result is not None:
        start,end = regex_result.span()
        return link_comment[:end]
    return link_comment


def get_comment_id(link_comment):
    regex_result = re.search(r"\?comment_id=\d+", link_comment)
    if regex_result is None:
        return None
    start, end = regex_result.span()
    string_comment_id = link_comment[start:end]
    regex_result_2 = re.search(r"\d+", string_comment_id)
    if regex_result is None:
        return None
    start,end = regex_result_2.span()
    return string_comment_id[start:end]


def get_reply_id(link_reply):
    regex_result = re.search(r"&reply_comment_id=\d+", link_reply)
    if regex_result is None:
        return None
    start,end = regex_result.span()
    string_reply_id = link_reply[start:end]
    regex_result_2 = re.search(r"\d+", string_reply_id)
    if regex_result is None:
        return None
    start,end = regex_result_2.span()
    return string_reply_id[start:end]


def save_dialogue(data, dir_save_data):
    file_name = data["dialogue_id"] + ".json"
    file_name_save = dir_save_data + file_name
    json.dump(data, open(file_name_save, "w", encoding="utf-8"), indent=4, ensure_ascii=False)


def generate_dialogue(file, dir_save_data, *args):
    data = json.load(open(file, "r", encoding="utf-8"))
    post_id = data["_id"]
    list_dialogue = []
    # print(len(data["comment"]))
    for main_comment in data["comment"]:
        for reply in main_comment["replies"]:
            main_comment_copy = main_comment.copy()
            main_comment_copy["comment_id"] = get_comment_id(main_comment_copy["link_to_reply"])
            reply["link_to_reply"] = process_link_reply(reply["link_to_reply"])
            reply["reply_id"] = get_reply_id(reply["link_to_reply"])
            main_comment_copy["replies"] = reply
            main_comment_copy["link_to_reply"] = process_link_comment(main_comment_copy["link_to_reply"])
            main_comment_copy["dialogue_id"] = str(post_id) + "_" + main_comment_copy["comment_id"] + "_" + reply[
                "reply_id"]
            if not len(args):
                main_comment_copy["account_comment"] = None
            else:
                main_comment_copy["account_comment"] = args[0]
            save_dialogue(main_comment_copy, dir_save_data)
            list_dialogue.append(main_comment_copy)

    print(len(list_dialogue))
    return list_dialogue

list_dialogue = generate_dialogue(r"E:\2575884495812741_5614931531908007.json", r"E:/dialogue_facebook/")



