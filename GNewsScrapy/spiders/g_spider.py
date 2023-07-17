import hashlib
from pathlib import Path
import scrapy
from GNewsScrapy.items import GnewsscrapyItem

class GnewsSpider(scrapy.Spider):
    name = "gnews"
    UA = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36' }
    Referer = { 'Referer': 'https://ogs.google.com/' }

    def start_requests(self):
        urls = [
            "https://news.google.com",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse, headers={**self.UA, **self.Referer})

    def parse(self, response):
        top_story_link = response.css("div.n3GXRc a.aqvwYd::attr(href)").get()
        print(top_story_link)
        if top_story_link is not None:
            self.Referer = { 'Referer': 'https://news.google.com/' }
            yield response.follow(top_story_link, callback=self.parse_top_story, headers={**self.UA, **self.Referer})

    def parse_top_story(self, response):
        for article in response.css("article.IBr9hb"):
            item = GnewsscrapyItem()
            item['link'] = "https://news.google.com/" + article.css("div.XlKvRb a::attr(href)").get()[2:]
            item['link_hash'] = hashlib.md5(item['link'].encode("utf-8")).hexdigest()
            #item['final_link'] = response.url
            #item['final_link'] = response.headers['Location'].decode("utf-8")
            #item['final_link'] = response.css("div.m2L3rb.eLNT1d a::attr(href)").get()
            item['title'] = article.css("h4::text").get()
            item['figure'] = article.css("figure img::attr(src)").get()
            item['icon'] = article.css("div.MCAGUe img.msvBD.zC7z7b::attr(src)").get()
            item['alt_icon'] = article.css("div.MCAGUe div.oovtQ img::attr(src)").get()
            item['icon_title'] = article.css("div.MCAGUe div.vr1PYe::text").get()
            item['time'] = article.css("div.UOVeFe time::attr(datetime)").get()
            item['downloaded'] = False
            item['skip'] = False

            item['image_urls'] = [item['figure']]
            yield item


