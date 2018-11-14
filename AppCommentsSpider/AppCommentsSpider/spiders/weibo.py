# -*- coding: utf-8 -*-
import scrapy
import json
import math
from items import WeibospiderItem, WeibospiderItemLoader


class WeiBoSpider(scrapy.Spider):
    name = 'weibo'
    allowed_domains = ['https://m.weibo.cn/api/']
    redis_key = 'weibo:start_urls'
    # user_name(在此填写登陆微博的账号)
    user_name = ''
    # password(在此填写登陆微博的密码)
    password = ''
    # uid是需要爬取博主的uid,可以在博主的微博主页得到,这里获得的是狼人杀微博的uid
    uid = '6285336793'

    tab_id = ''
    uid_url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value={}'
    cards = 'https://m.weibo.cn/api/container/getIndex?type=uid&value={}&containerid={}&page={}'
    comments = 'https://m.weibo.cn/api/comments/show?id={}&page={}'
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "passport.weibo.cn",
        "Origin": "https://passport.weibo.cn",
        "Referer": "https://passport.weibo.cn/signin/login?entry=mweibo&res=wel&wm=3349&r=https%3A%2F%2Fm.weibo.cn%2F",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36",
    }
    post_data = {
        "username": user_name,
        "password": password,
        "savestate": "1",
        "r": "https%3A%2F%2Fm.weibo.cn%2F",
        "ec": "0",
        "pagerefer": "https%3A%2F%2Fpassport.weibo.cn%2Fsignin%2Fwelcome%3Fentry%3Dmweibo%26r%3Dhttps%253A%252F%252Fm.weibo.cn%252F",
        "entry": "mweibo",
        "prelt": "0",
        "wentry": "",
        "loginfrom": "",
        "client_id": "",
        "code": "",
        "qq": "",
        "mainpageflag": "1",
        "hff": "",
        "hfp": ""
    }

    def start_requests(self):
        url = 'https://passport.weibo.cn/signin/welcome?'
        return [scrapy.Request(url, callback=self.login, dont_filter=True)]

    def login(self, response):
        """
        请求登录并获得cookie
        :param response:
        :return:
        """
        url = 'https://passport.weibo.cn/sso/login'
        return [scrapy.FormRequest(url=url, formdata=self.post_data, headers=self.headers,
                                   callback=self.check_login, dont_filter=True)]

    def check_login(self, response):
        """
        判断登录成功之后开始爬取api的数据
        :param response:
        :return:
        """
        text_json = json.loads(response.text)
        if text_json['retcode'] == 20000000:
            print('登陆成功')
            yield scrapy.Request(self.uid_url.format(self.uid), callback=self.parse, dont_filter=True)
        else:
            print('登陆失败')

    def parse(self, response):
        """
        爬取博主的所发的微博部分
        :param response:
        :return:
        """
        user_data = json.loads(response.text)
        tabs = user_data['data']['tabsInfo']['tabs']
        for tab in tabs:
            if tab['tab_type'] == 'weibo':
                self.tab_id = tab.get('containerid')
        cards_data = self.cards.format(self.uid, self.tab_id, '1')
        yield scrapy.Request(cards_data, self.parse_cards_info, dont_filter=True)

    def parse_cards_info(self, response):
        """
        获得博主所发的微博的信息
        :param response:
        :return:
        """
        cards = json.loads(response.text)
        cards_total = cards.get('data').get('cardlistInfo').get('total')
        pages = cards_total / 10
        for i in range(int(pages) + 1):
            cards_url = self.cards.format(self.uid, self.tab_id, i + 1)
            yield scrapy.Request(cards_url, self.parse_cards)

    def parse_cards(self, response):
        """
        处理博主发的每一条微博
        :param response:
        :return:
        """
        cards = json.loads(response.text)
        for card in cards.get('data').get('cards'):
            if 'mblog' in card:
                # 没有评论的微博就不爬取了
                if card.get('mblog').get('comments_count'):
                    text = card.get('mblog').get('text')
                    created_at = card.get('mblog').get('created_at')
                    attitudes = card.get('mblog').get('attitudes_count')
                    para = {'text': text, 'created_at': created_at, 'attitudes': attitudes}
                    card_id = card.get('mblog').get('id')
                    # 微博评论的api中每10行成一页，可以计算出总的页数
                    comments_num = card.get('mblog').get('comments_count')
                    pages = math.ceil(comments_num/10)
                    for i in range(pages):
                        yield scrapy.Request(self.comments.format(card_id, i+1), meta=para,
                                             callback=self.parse_comments)

    def parse_comments(self, response):
        """
        处理每条微博下的评论
        :param response:
        :return:
        """
        text = response.meta.get("text", "")
        created_at = response.meta.get("created_at", "")
        attitudes = response.meta.get("attitudes", "")
        comment_items = json.loads(response.text)
        for comment_item in comment_items['data']['data']:
            item_loader = WeibospiderItemLoader(item=WeibospiderItem(), response=response)
            user_name = comment_item.get('user').get('screen_name')
            comment_time = comment_item.get('created_at')
            comment = comment_item.get('text')
            item_loader.add_value('url', response.url)
            item_loader.add_value('post_text', text)
            item_loader.add_value('post_time', created_at)
            item_loader.add_value('attitudes', attitudes)
            item_loader.add_value('user_name', user_name)
            item_loader.add_value('comment_time', comment_time)
            item_loader.add_value('comment', comment)
            reviews_loader = item_loader.load_item()
            yield reviews_loader
