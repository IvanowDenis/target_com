# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TargetComItem(scrapy.Item):
    title = scrapy.Field()
    price = scrapy.Field()
    images = scrapy.Field()
    description = scrapy.Field()
    highlights = scrapy.Field()
    last_question = scrapy.Field()
    last_answer = scrapy.Field()
