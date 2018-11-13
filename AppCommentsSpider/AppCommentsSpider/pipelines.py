# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import MySQLdb
import logging
import MySQLdb.cursors
from twisted.enterprise import adbapi
logger = logging.getLogger(__name__)


class AppcommentsspiderPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        """
        载入数据库的配置
        :param settings:
        :return:
        """
        dbparms = dict(
            host=settings["MYSQL_HOST"],
            db=settings["MYSQL_DBNAME"],
            user=settings["MYSQL_USER"],
            passwd=settings["MYSQL_PASSWORD"],
            charset='utf8mb4',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)
        return cls(dbpool)

    def process_item(self, item, spider):
        """
        使用twisted将mysql插入变成异步执行
        :param item:
        :param spider:
        :return:
        """
        for field in item.fields:
            item.setdefault(field, '')
        query = self.dbpool.runInteraction(self.do_insert, item)
        # 处理异常
        query.addErrback(self.handle_error, item, spider)

    def handle_error(self, failure, item, spider):
        # log中写入异步插入的异常
        logging.error(failure)

    def do_insert(self, cursor, item):
        """
        执行具体的插入
        根据不同的item构建不同的sql语句并插入到mysql中
        :param cursor:
        :param item:
        :return:
        """
        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, params)
