# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GnewsscrapyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    link = scrapy.Field()
    link_hash = scrapy.Field()
    final_link = scrapy.Field()
    title = scrapy.Field()
    figure = scrapy.Field()
    icon = scrapy.Field()
    alt_icon = scrapy.Field()
    icon_title = scrapy.Field()
    time = scrapy.Field()
    downloaded = scrapy.Field()
    skip = scrapy.Field()

    image_urls = scrapy.Field()
    images = scrapy.Field()
