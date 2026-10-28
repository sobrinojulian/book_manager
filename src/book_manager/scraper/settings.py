BOT_NAME = "book_manager_scraper"

SPIDER_MODULES = ["book_manager.scraper.spiders"]
NEWSPIDER_MODULE = "book_manager.scraper.spiders"

ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 1
AUTOTHROTTLE_ENABLED = True

ITEM_PIPELINES = {
  "book_manager.scraper.pipelines.CuspideJsonPipeline": 300,
}