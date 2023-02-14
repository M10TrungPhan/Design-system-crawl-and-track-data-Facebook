from apis.routes.base_route import BaseRoute
from service.pages_controller import PageController
from service.manage_account_facebook import ManageAccountFacebook
from object.account_fb_request import AccountFacebookRequest


class ManualRoute(BaseRoute):

    def __init__(self):
        super(ManualRoute, self).__init__(prefix="")
        self.manager_account = ManageAccountFacebook()
        # self.pages_controller = PageController()

    def create_account(self, account: AccountFacebookRequest):
        return self.manager_account.add_account_facebook(account)

    def remove_account(self, account: AccountFacebookRequest):
        return self.manager_account.remove_account_facebook(account)

    def update_information_account(self, account: AccountFacebookRequest):
        return self.manager_account.update_information_account_api(account)

    def get_information_account(self, account: AccountFacebookRequest):
        return self.manager_account.check_information_account(account)

    def get_information_all_account(self):
        return self.manager_account.get_information_all_account()

    def create_routes(self):
        router = self.router

        @router.put("/facebook/account")
        async def create_account(account: AccountFacebookRequest):
            output = await self.wait(self.create_account, account)
            return output

        @router.post("/facebook/account")
        async def update_information_account(account: AccountFacebookRequest):
            output = await self.wait(self.update_information_account, account)
            return output

        @router.delete("/facebook/account")
        async def remove_account(account: AccountFacebookRequest):
            output = await self.wait(self.remove_account, account)
            return output

        @router.get("/facebook/account")
        async def get_information_account(account: AccountFacebookRequest):
            output = await self.wait(self.get_information_account, account)
            return output

        @router.get("/facebook/all_account/")
        async def get_information_all_account():
            output = await self.wait(self.get_information_all_account)
            return output
