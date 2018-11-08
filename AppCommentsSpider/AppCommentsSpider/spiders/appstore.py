# -*- coding: utf-8 -*-
from scrapy.spiders import XMLFeedSpider
from items import AppstorespiderItem, AppstorespiderItemLoader


class AppstoreSpider(XMLFeedSpider):
    name = 'appstore'
    allowed_domains = ['https://itunes.apple.com/']
    namespaces = [('atom', 'http://www.w3.org/2005/Atom'), ('im', 'http://itunes.apple.com/rss')]
    # id后面的参数是app在appstore下面的id,这里是爬取的qq炫舞的评论为例,它的id是1219233424
    start_urls = [
        'https://itunes.apple.com/cn/rss/customerreviews/page={}/id=1219233424/sortby=mostrecent/xml'.format(i)
        for i in range(1, 11)]
    iterator = 'xml'
    itertag = 'atom:entry'

    def parse_node(self, response, selector):
        """
        提取appstore的api中的500条评论
        :param selector:
        :param response:
        :return:
        """
        item_loader = AppstorespiderItemLoader(item=AppstorespiderItem(), selector=selector)
        item_loader.add_value('url', response.url)
        item_loader.add_xpath('comment_time', 'atom:updated/text()')
        item_loader.add_xpath('title', 'atom:title/text()')
        item_loader.add_xpath('comment', 'atom:content/text()')
        item_loader.add_xpath('rate', 'im:rating/text()')
        item_loader.add_xpath('version', 'im:version/text()')
        item_loader.add_xpath('user_name', 'atom:author/atom:name/text()')
        reviews_loader = item_loader.load_item()
        yield reviews_loader
