# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class IphoneSpiderItem(scrapy.Item):
    sku = scrapy.Field()
    price = scrapy.Field()
    name = scrapy.Field()
    seller = scrapy.Field()
    model = scrapy.Field()
    color = scrapy.Field()
    memory = scrapy.Field()
    url = scrapy.Field()

