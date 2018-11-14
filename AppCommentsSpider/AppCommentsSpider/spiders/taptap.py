# -*- coding: utf-8 -*-
from scrapy_redis.spiders import RedisSpider
from items import TaptapspiderItem, TaptapspiderItemLoader
import scrapy


class TaptapSpider(RedisSpider):
    name = 'taptap'
    allowed_domains = ['taptap.com']
    redis_key = 'taptap:start_urls'

    def parse(self, response):
        """
        获取评论的页面
        :param response:
        :return:
        """
        review_url = response.xpath('//div[@class="main-header-tab"]/ul/li[2]/a/@href').extract_first("")
        if review_url:
            yield scrapy.Request(url=review_url, callback=self.parse_reviews, dont_filter=True)

    def parse_reviews(self, response):
        """
        抓取页面中的内容
        :param response:
        :return:
        """
        next_url = response.xpath('//div[@class="main-body-footer"]//ul/li[last()]/a/@href').extract_first("")
        selector = scrapy.Selector(response)
        reviews = selector.xpath('//*[contains(@class, "taptap-review-item")]')
        for review in reviews:
            item_loader = TaptapspiderItemLoader(item=TaptapspiderItem(), selector=review)
            item_loader.add_value("url", response.url)
            item_loader.add_xpath("user_name", '@data-user')
            item_loader.add_xpath("comment", 'div/div[3]//text()')
            item_loader.add_xpath("comment_time", 'div/div[1]/a/span/span[2]/text()')
            item_loader.add_xpath("phone", 'div/div[4]/span/text()')
            item_loader.add_xpath("like_it", 'div/div[4]/ul/li[2]/button/span/text()')
            item_loader.add_xpath("dislike_it", 'div/div[4]/ul/li[3]/button/span/text()')
            item_loader.add_xpath("rate", 'div/div[2]/i[1]/@style')
            reviews_loader = item_loader.load_item()
            yield reviews_loader
        if next_url:
            yield scrapy.Request(url=next_url, callback=self.parse_reviews)


