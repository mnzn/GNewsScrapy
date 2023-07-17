# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import scrapy
import pymongo
import logging
from itemadapter import ItemAdapter
from scrapy.http.request import NO_CALLBACK
from scrapy.utils.defer import maybe_deferred_to_future
from scrapy.exceptions import DropItem
import os, sys
from scrapy.pipelines.images import ImagesPipeline

#class GnewsImagesPipeline(ImagesPipeline):
#    def file_path(self, request, response=None, info=None, *, item=None):
#        return item['link_hash'] + "/figure.webp"
#
#    def get_media_requests(self, item, info):
#        self.UA = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36' }
#        self.Referer = { 'Referer': 'https://news.google.com/' }
#        for image_url in item["image_urls"]:
#            yield scrapy.Request(url=image_url, headers={**self.UA, **self.Referer})


class GnewsscrapyPipeline:
    def __init__(self):
        self.client = pymongo.MongoClient('localhost', 27017)
        self.db = self.client["gnews"]
        self.collection = self.db["headlines"]
        self.UA = { 'User-Agent': 'curl/8.0.1' }
        self.Referer = { 'Referer': 'https://news.google.com/' }

    def is_exist(self, link_hash):
        myquery = { "link_hash": link_hash }
        result = self.collection.count_documents(myquery)
        if result != 0:
            return True
        else:
            return False

    async def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if self.is_exist(adapter['link_hash']):
            raise DropItem(f"Drop exist item: {adapter}")
        else:
            request = scrapy.Request(url=adapter['link'], meta={'dont_redirect': True, 'handle_httpstatus_list': [301]}, callback=NO_CALLBACK, headers={**self.UA, **self.Referer})
            response = await maybe_deferred_to_future(
                spider.crawler.engine.download(request)
            )
            if response.status != 301:
                logging.warning("Async/Await request return error:%d", response.status)
                raise DropItem(f"Drop error item: {adapter}")

            adapter['final_link'] = response.headers['Location'].decode("utf-8")
            logging.warning("Got final_link:%s", adapter['final_link'])

            try:
                self.collection.insert_one(adapter.asdict())
                logging.warning("Inserted headline:%s", adapter["final_link"])

                #os.mkdir("/root/GNewsFront/public/news_resource/pics/"+item['link_hash'], 0o666)

                return item
            except:
                logging.warning("Duplicate headline:%s", adapter["final_link"])
                raise DropItem(f"Drop duplicate headline: {adapter}")

    def close_spider(self, spider):
        if self.client:
            self.client.close()

    def __del__(self):
        if self.client:
            self.client.close()
