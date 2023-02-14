from service.crawl_video_facebook import CrawlVideoFacebookService
from service.manage_account_facebook import ManageAccountFacebook
import time
mn = ManageAccountFacebook()
# mn.update_information_for_all_account()
mn.start()
for _ in range(20):
    crawl_watch = CrawlVideoFacebookService("txnnxt2k@gmail.com",
                                            r"\\smb-ai.tmt.local\Public-AI\Public\Data\Data_GROUP_FACEBOOK_2/")
    crawl_watch.process_video_facebook()
    time.sleep(60)

