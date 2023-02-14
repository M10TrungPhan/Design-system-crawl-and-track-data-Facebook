
from urllib.request import Request
from service.crawl_facebook import CrawlFacebook
from object.account_fb_request import PageRequest
from database.fanpage_db import FanpageDB


class PageController:
    def __init__(self,):
        self.fanpage_db = FanpageDB()
        self.facebook_crawler = CrawlFacebook()
    

    def get_page_info(self,id_page):
        page_info = self.fanpage_db.get_info_by_id(id_page)
        return page_info

    def create_page(self, page: PageRequest):
        self.fanpage_db.add_page(page)
    
    def pause_crawl_page(self):
        pass
    
    def stop_crawl_page(self):
        pass

    def start_crawl_page(self, page: PageRequest):
        self.facebook_crawler(page.url_page)

    def start_current_page(self):
        pass

    def start_crawl_pending_pages(self):
        pass