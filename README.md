# app_comments_spider
&emsp;&emsp;基于redis_scrapy的爬虫，用来获得微博博主的微博评论、taptap上某款游戏评论、百度贴吧帖子评论和appstore上api给的最近500个评论。
## 环境与配置
&emsp;&emsp;python为3.6版本，所需的python相关包在requirements下，环境配置好后还需要在AppCommentsSpider/settings中配置mysql和redis的连接。
## 启动
&emsp;&emsp;爬虫前需要根据item中的字段在数据库里创建相应的表和表结构，然后在launch中开启爬虫命令。
### Taptap爬虫
&emsp;&emsp;运行launch之后，scrapy会监听redis中的taptap:start_urls这个key，需要手动在redis中加入一个start_urls(这里以王者荣耀的taptap主页为例):
```
127.0.0.1:6379> lpush taptap:start_urls https://www.taptap.com/app/2301
```
### appstore的api爬虫
&emsp;&emsp;这里只是通过appstore给的api接口获取某个app的最近500条评论，爬取前需要获得这个app的id，在[appstore应用](https://itunes.apple.com/cn/genre/%E9%9F%B3%E4%B9%90/id36)中找到对应的app，这里以QQ炫舞为例，进入[它的页面](https://itunes.apple.com/cn/app/qq%E7%82%AB%E8%88%9E/id1219233424?mt=8)之后，浏览器url中包含的1219233424就是这个游戏的id。把它填写在AppCommentsSpider/spiders/appstore.py中的start_urls中，然后运行launch获得评论。
### Baidu贴吧爬虫
&emsp;&emsp;运行launch之后，scrapy会监听redis中的tieba:start_urls这个key，需要手动在redis中加入一个start_urls(这里以王者荣耀的tieba为例):
```
127.0.0.1:6379> lpush tieba:start_urls https://tieba.baidu.com/f?kw=%CD%F5%D5%DF%C8%D9%D2%AB&fr=ala0&tpl=5
```
&emsp;&emsp;贴吧爬虫里面通过拼接url在不需要登陆的情况下获得楼主的所有评论，另外，由贴吧请求下来的response.text文件中，内容主体部分通过<!---->注释掉了，没法用xpath或者css解析，这里用了正则匹配。
### Weibo爬虫
&emsp;&emsp;这里直接用微博给的api进行爬虫，爬取api要先登陆获得cookie，AppCommentsSpider/settings也需要将cookie打开:`COOKIES_ENABLED = True`，这里登陆选择的是[手机登陆页面](https://passport.weibo.cn/signin/welcome?)，谷歌浏览器勾选F12->NetWork->Preserve log，然后进行一次实际登陆。  
&emsp;&emsp;实际登陆过程中发现，微博将表单post到了https://passport.weibo.cn/sso/login 这个网址，通过构建formdata和header模拟登陆便可以登陆微博，登陆成功之后微博返回的rtncode为20000000，据此可以判断是否成功登陆。  
&emsp;&emsp;博主首页、博主发的所有微博、每个微博下的评论都有对应的api(这里以狼人杀官方博主为例，它的微博uid为6303234698):  
&emsp;&emsp;博主的首页api是这个地址:https://m.weibo.cn/api/container/getIndex?type=uid&value=6303234698  
&emsp;&emsp;它的所发微博的api(第一页):https://m.weibo.cn/api/container/getIndex?type=uid&value=6303234698&containerid=1076036303234698&page=1  
&emsp;&emsp;某一条微博下面的评论api(第一页):https://m.weibo.cn/api/comments/show?id=4301991066849269&page=1  
&emsp;&emsp;爬虫前，在/AppCommentsSpider/spiders/weibo.py设置好uid、账号、密码之后就可以运行launch开始爬虫，由于已经打开了scrapy的cookie，后面可以直接带上cookie访问微博的api，最好限制一下访问速度，不然会被微博限速。
## 结语
&emsp;&emsp;上述网站都会不定期做相应的反爬虫处理，所以爬虫的代码也需要及时更新。反爬虫方面，本项目只做了随机user_agent和分布式爬取。单机器爬取时也可以适当做些限速处理。
