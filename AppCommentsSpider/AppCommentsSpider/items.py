# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
import re
import datetime
import time
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags


def go_remove_tag(value):
    """
    去掉其它的符号
    :param value:
    :return:
    """
    content = remove_tags(value)
    filter_value = re.sub(r'[\t\r\n\s]', '', content).strip()
    if filter_value:
        return filter_value


def get_rate(value):
    """
    提取归一化后的评价
    :param value:
    :return:
    """
    match_re = re.match(".*?(\d+).*", value)
    nums = int(match_re.group(1))
    return nums / 70


def get_ios_rate(value):
    """
    获得苹果评论的归一化评论
    :param value:
    :return:
    """
    return int(value) / 5


def transfer_time(value):
    """
    格式化时间
    :param value:
    :return:
    """
    filter_value = re.sub('T', ' ', value)[0:19]
    return filter_value


def get_format_datetime(value):
    """
    :param value: 微博api的时间(created at)
    :return: 格式化好的时间
    """
    now = datetime.datetime.now()
    ymd = now.strftime("%Y-%m-%d")
    y = now.strftime("%Y")
    if "今天" in value:
        mdate = time.mktime(time.strptime(ymd + value, '%Y-%m-%d今天 %H:%M'))
        newdate = datetime.datetime.fromtimestamp(mdate)
    elif "月" in value:
        mdate = time.mktime(time.strptime(y + value, '%Y%m月%d日 %H:%M'))
        newdate = datetime.datetime.fromtimestamp(mdate)
    elif "分钟前" in value:
        newdate = now - datetime.timedelta(minutes=int(value[:-3]))
    elif "秒前" in value:
        newdate = now - datetime.timedelta(minutes=int(value[:-2]))
    elif "-" in value:
        if value.count('-') == 1:
            mdate = time.mktime(time.strptime(y + "-" + value, '%Y-%m-%d'))
            newdate = datetime.datetime.fromtimestamp(mdate)
        else:
            mdate = time.mktime(time.strptime(value, '%Y-%m-%d'))
            newdate = datetime.datetime.fromtimestamp(mdate)
    elif "昨天" in value:
        mdate = time.mktime(time.strptime(ymd + value, '%Y-%m-%d昨天 %H:%M'))
        newdate = datetime.datetime.fromtimestamp(mdate) - datetime.timedelta(days=1)
    elif "小时前" in value:
        newdate = now - datetime.timedelta(hours=int(value[:-3]))
    else:
        newdate = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M")
    return str(newdate)[0:19]


class AppstorespiderItemLoader(ItemLoader):
    """
    Appstore评论爬虫itemloader
    """
    pass


class AppstorespiderItem(scrapy.Item):
    """
    Appstore评论爬虫的item
    """
    url = scrapy.Field(
        output_processor=TakeFirst(),
    )
    user_name = scrapy.Field(
        output_processor=TakeFirst(),
    )
    comment_time = scrapy.Field(
        input_processor=MapCompose(transfer_time),
        output_processor=TakeFirst(),
    )
    title = scrapy.Field(
        output_processor=TakeFirst(),
    )
    comment = scrapy.Field(
        input_processor=MapCompose(go_remove_tag),
        output_processor=TakeFirst(),
    )
    rate = scrapy.Field(
        input_processor=MapCompose(get_ios_rate),
        output_processor=TakeFirst(),
    )
    version = scrapy.Field(
        output_processor=TakeFirst(),
    )

    def get_insert_sql(self):
        """
        Appstore中的数据执行mysql插入
        :return:
        """
        insert_sql = """
            insert into appstore(url,user_name,comment_time,title,comment,rate,version) 
            VALUES (%s, %s, %s, %s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE url=VALUES(url),user_name=VALUES(user_name),comment_time=VALUES(comment_time),
            title=VALUES(title),comment=VALUES(comment),rate=VALUES(rate), version=VALUES(version)

        """
        params = (self['url'], self['user_name'], self['comment_time'], self['title'], self['comment'],
                  self['rate'], self['version'])
        return insert_sql, params


class TiebaspiderItemLoader(ItemLoader):
    """
    Baidu贴吧的itemloader
    """
    pass


class TiebaspiderItem(scrapy.Item):
    """
    Baidu贴吧楼主帖子的items
    """
    url = scrapy.Field(
        output_processor=TakeFirst(),
    )
    title = scrapy.Field(
        output_processor=TakeFirst(),
    )
    user_name = scrapy.Field(
        output_processor=TakeFirst(),
    )
    first_comment_time = scrapy.Field(
        output_processor=TakeFirst(),
    )
    phone_system = scrapy.Field(
        output_processor=TakeFirst(),
    )
    comments = scrapy.Field(
        input_processor=MapCompose(go_remove_tag),
        output_processor=Join(','),
    )

    def get_insert_sql(self):
        """
        Baidu贴吧楼主帖子数据执行mysql插入
        :return:
        """
        insert_sql = """
            insert into tieba(url,title,user_name,phone_system,first_comment_time,comments) 
            VALUES (%s, %s, %s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE url=VALUES(url),title=VALUES(title),user_name=VALUES(user_name),
            phone_system=VALUES(phone_system),first_comment_time=VALUES(first_comment_time),comments=VALUES(comments)

        """
        params = (self['url'], self['title'], self['user_name'], self['phone_system'], self['first_comment_time'],
                  self['comments'])
        return insert_sql, params


class TaptapspiderItemLoader(ItemLoader):
    """
    Taptap的itemloader
    """
    pass


class TaptapspiderItem(scrapy.Item):
    """
    Taptap评论的items
    """
    url = scrapy.Field(
        output_processor=TakeFirst(),
    )
    user_name = scrapy.Field(
        output_processor=TakeFirst(),
    )
    comment = scrapy.Field(
        input_processor=MapCompose(go_remove_tag),
        output_processor=Join(','),
    )
    comment_time = scrapy.Field(
        output_processor=TakeFirst(),
    )
    phone = scrapy.Field(
        output_processor=TakeFirst(),
    )
    like_it = scrapy.Field(
        output_processor=TakeFirst(),
    )
    dislike_it = scrapy.Field(
        output_processor=TakeFirst(),
    )
    rate = scrapy.Field(
        input_processor=MapCompose(get_rate),
        output_processor=TakeFirst(),
    )

    def get_insert_sql(self):
        """
        Taptap数据执行mysql插入
        :return:
        """
        insert_sql = """
            insert into taptap(url,user_name,comment,comment_time,phone,like_it,dislike_it,rate) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE url=VALUES(url),user_name=VALUES(user_name),comment=VALUES(comment),
            comment_time=VALUES(comment_time),phone=VALUES(phone),like_it=VALUES(like_it),dislike_it=VALUES(dislike_it),
            rate=VALUES(rate)
        """
        params = (self['url'], self['user_name'], self['comment'], self['comment_time'], self['phone'],
                  self['like_it'], self['dislike_it'], self['rate'])
        return insert_sql, params


class WeibospiderItemLoader(ItemLoader):
    """
    Weibo的itemloader
    """
    pass


class WeibospiderItem(scrapy.Item):
    """
    Weibo评论的items
    """
    url = scrapy.Field(
        output_processor=TakeFirst(),
    )
    post_text = scrapy.Field(
        input_processor=MapCompose(go_remove_tag),
        output_processor=Join(','),
    )
    post_time = scrapy.Field(
        input_processor=MapCompose(get_format_datetime),
        output_processor=TakeFirst(),
    )
    attitudes = scrapy.Field(
        output_processor=TakeFirst(),
    )
    user_name = scrapy.Field(
        output_processor=TakeFirst(),
    )
    comment_time = scrapy.Field(
        input_processor=MapCompose(get_format_datetime),
        output_processor=TakeFirst(),
    )
    comment = scrapy.Field(
        input_processor=MapCompose(go_remove_tag),
        output_processor=Join(','),
    )

    def get_insert_sql(self):
        """
        Weibo评论数据执行mysql插入
        :return:
        """
        insert_sql = """
            insert into weibo(url,post_text,post_time,attitudes,user_name,comment_time,comment) 
            VALUES (%s, %s, %s, %s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE url=VALUES(url),post_text=VALUES(post_text),post_time=VALUES(post_time),
            attitudes=VALUES(attitudes),user_name=VALUES(user_name),comment_time=VALUES(comment_time),comment=VALUES(comment)
        """
        params = (self['url'], self['post_text'], self['post_time'], self['attitudes'], self['user_name'],
                  self['comment_time'], self['comment'])
        return insert_sql, params
