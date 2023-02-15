import time

from service.crawl_facebook import CrawlFacebook

from service.manage_account_facebook import ManageAccountFacebook


if __name__ == "__main__":
    list_url = ["https://www.facebook.com/groups/Grouptinhte", "https://www.facebook.com/groups/441249175921600",
                "https://www.facebook.com/ttxltt", "https://www.facebook.com/groups/929563144068596",
                "https://www.facebook.com/groups/phanbien/", "https://www.facebook.com/groups/2542993789352101/",
                "https://www.facebook.com/groups/mela.com.vn/", "https://www.facebook.com/groups/1065116420221723"]

    manage_account = ManageAccountFacebook()
    manage_account.update_information_for_all_account()
    manage_account.start()

    for url_page in list_url:
        crawl_fb = CrawlFacebook(url_page)
        crawl_fb.start()
        crawl_fb.join()
        time.sleep(1*60)
    manage_account.flag_finish = True


