# -*- coding: utf-8 -*-
from scrapy_redis.spiders import RedisSpider
from items import TaptapspiderItemLoader, TiebaspiderItem
from urllib import parse
import scrapy
import re


class TiebaSpider(RedisSpider):
    name = 'tieba'
    allowed_domains = ['https://tieba.baidu.com/']
    redis_key = 'tieba:start_urls'

    def parse(self, response):
        """
        获取贴吧的页面，获得本页所有的帖子
        :param response:
        :return:
        """
        all_urls = re.findall('href="(/p/\d+)"', response.text, re.DOTALL)
        all_urls = [parse.urljoin(response.url, url)+'?see_lz=1' for url in all_urls]
        for url in all_urls:
            yield scrapy.Request(url, callback=self.parse_tiezi)
        next_page = re.findall('<a href="(//tieba.baidu.com/f\?kw=.*)" class="next', response.text)[0]
        next_page = parse.urljoin(response.url, next_page)
        if next_page:
            yield scrapy.Request(url=next_page, callback=self.parse, dont_filter=True)

    def parse_tiezi(self, response):
        """
        每个帖子获取楼主的帖子信息
        :param response:
        :return:
        """
        item_loader = TaptapspiderItemLoader(item=TiebaspiderItem(), response=response)
        item_loader.add_value("url", response.url)
        item_loader.add_xpath("title", '//*[@id="j_core_title_wrap"]/h3/@title')
        item_loader.add_xpath("user_name", '//*[@id="j_p_postlist"]/div[1]/div[1]/ul/li[3]/a/text()')
        selector = scrapy.Selector(response)
        floors = selector.xpath('//*[contains(@class, "l_post_bright")]')
        comments_list = []
        first_comment_time = ''
        phone_system = ''
        is_first = False
        for floor in floors:
            comment = floor.xpath('div[2]/div[1]/cc/div//text()').extract()
            comments_list.append(','.join(comment).strip())
            spans = floor.xpath('div[2]//div[@class="post-tail-wrap"]/span')
            if not is_first:
                is_first = True
                if len(spans) == 3:
                    first_comment_time = spans[2].xpath('text()').extract_first("")
                if len(spans) == 4:
                    first_comment_time = spans[3].xpath('text()').extract_first("")
            if len(spans) == 4:
                phone_system = spans[1].xpath('a/text()').extract_first("")
        item_loader.add_value("comments", ','.join(comments_list))
        item_loader.add_value("first_comment_time", first_comment_time)
        item_loader.add_value("phone_system", phone_system)
        reviews_loader = item_loader.load_item()
        yield reviews_loader


