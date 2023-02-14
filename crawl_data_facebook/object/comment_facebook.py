from types import new_class
import requests
import json

from object.token_and_cookies import TokenAndCookies


class CommentFacebook:

    def __init__(self, id_comment, token_and_cookies: TokenAndCookies):
        self.id_comment = id_comment
        self.token_and_cookies = token_and_cookies
        self.main_comment = None
        self.user_comment = None
        self.reply = []
        self.next_comment = ""

    def requests_first_comment(self):

        url = f"https://graph.facebook.com/v15.0/{self.id_comment}/comments?filter=stream" \
              f"&access_token={self.token_and_cookies.load_token_access()}&fields=message_tags,from,message"
        # ASSIGN COOKIES FOR REQUEST
        requestJar = requests.cookies.RequestsCookieJar()
        for each in self.token_and_cookies.load_cookies():
            requestJar.set(each["name"], each["value"])
        jsonformat = None
        # REQUESTS TO GRAPH API
        for i in range(5):
            try:
                response = requests.get(url, cookies=requestJar)
                jsonformat = json.loads(response.text)

                # CHECK ERROR FOR RESPONSE
                if self.check_token_valid(jsonformat):
                    continue
                break
            except:
                continue
        if jsonformat is None:
            return

        # ASSIGN NEXT URL REQUEST FOR COMMENT
        try:
            self.next_comment = jsonformat["paging"]["next"]
        except KeyError:
            self.next_comment = None

        # COLLECT DATA
        try:
            for each in jsonformat["data"]:
                new_reply = {"tags": [i['name'] for i in each['message_tags']], "user": each["from"]["name"],
                             "text": each["message"]}
                self.reply.append(new_reply)
        except KeyError:
            pass

    def request_next_comment(self):
        # LOOP ALL PAGE FOR COMMENT
        while self.next_comment is not None:
            # ASSIGN COOKIES FOR REQUEST
            requestJar = requests.cookies.RequestsCookieJar()
            for each in self.token_and_cookies.load_cookies():
                requestJar.set(each["name"], each["value"])
            jsonformat = None
            # REQUEST FOR URL COMMENT
            for i in range(5):
                try:
                    response = requests.get(self.next_comment, cookies=requestJar)
                    jsonformat = json.loads(response.text)
                    # # CHECK ERROR FOR RESPONSE
                    if self.check_token_valid(jsonformat):
                        continue
                    break
                except:
                    continue
            if jsonformat is None:
                return
            # ASSIGN NEXT URL REQUEST FOR COMMENT
            try:
                self.next_comment = jsonformat["paging"]["next"]
            except KeyError:
                self.next_comment = None
            # COLLECT DATA
            try:
                for each in jsonformat["data"]:
                    if 'message_tags' not in each.keys():
                        tags = []
                    else:
                        tags = [i['name'] for i in each['message_tags']]
                    if len(each["message"]) < 1:
                        continue
                    new_reply = {"tags": tags, "user": each["from"]["name"], "text": each["message"]}
                    self.reply.append(new_reply)
            except KeyError:
                pass

    def check_token_valid(self, jsonformat):
        if "error" in jsonformat.keys():
            if jsonformat["error"]["code"] == 102:
                self.token_and_cookies.update_new_token()
                return True
            if jsonformat["error"]["code"] == 100:
                return False
            return False

    @property
    def dict_comment(self):
        return {"main_comment": {"user": self.user_comment, "text": self.main_comment},
                "replies": self.reply}

    def process_comment(self):
        self.requests_first_comment()
        self.request_next_comment()
        return self.dict_comment



