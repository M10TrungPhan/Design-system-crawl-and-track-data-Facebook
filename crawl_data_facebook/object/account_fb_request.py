
from pydantic import BaseModel
from typing import AnyStr, Optional, Dict,  List


class AccountFacebookRequest(BaseModel):
    username: AnyStr
    password: Optional[AnyStr]
    status: Optional[AnyStr]
    token_access: Optional[AnyStr]
    cookies: Optional[List[Dict]]
    account_name: Optional[AnyStr]

    def __init__(self, username: AnyStr, password: AnyStr = None, status: AnyStr = None,
                 token_access: Optional[AnyStr] = None, cookies: Optional[List[Dict]] = None,
                 account_name: Optional[AnyStr] = None):
        super(AccountFacebookRequest, self).__init__(username=username, password=password, status=status,
                                                     token_access=token_access, cookies=cookies,
                                                     account_name=account_name)
        self.username = username
        self.password = password
        self.status = status
        self.token_access = token_access
        self.cookies = cookies
        self.account_name = account_name


class PageRequest(BaseModel):
    name_page: AnyStr
    url_page: AnyStr
    status: Optional[AnyStr]
    last_update: Optional[AnyStr]

    def __init__(self, name_page: AnyStr, url_page: AnyStr, status: AnyStr = None, last_update: AnyStr = None, event=None,
                 flag=None):
        self.name_page = name_page
        self.url_page = url_page
        self.status = status
        self.last_update = last_update
        self.event = event
        self.flag = flag
