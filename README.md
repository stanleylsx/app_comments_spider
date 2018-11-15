# app_comments_spider
&emsp;&emsp;基于redis_scrapy的爬虫，用来获得微博博主的微博评论、taptap上某款游戏评论、百度贴吧帖子评论和appstore上api给的最近500个评论，去重策略是基于布隆过滤器(bloomfilter)，可以实现对上述爬虫的增量爬取和持久化爬取。
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
## 去重策略和持久化爬取
### 去重策略
&emsp;&emsp;在基于redis的scrapy爬虫框架中，redis承包了两个部分，一部分是request队列的管理，另外一部分是去重管理。前者是用list类型将requests存储在redis中，key的名字是XXX:requests，这个队列中的request等待客户端去消耗。后者是一个set的类型，key的名字叫做XXX:dupefilter，set本身是一个非重复的集合，每当有新的请求过来，redis都会将这个待爬虫网页的url计算指纹之后利用sadd添加至XXX:dupefilter中，如果里面没有重复的值就会返回1表示添加成功，否则返回false，这个过程会在scrapy_redis的dupefilter中RFPDupeFilter中的request_seen函数定义，所以在修改过滤规则的时候这个函数也是需要修改的一部分。  
&emsp;&emsp;利用redis中的set结构来做去重是一个保守无险的策略，但是在处理大数据的时候(数据量上亿)，这样的结构也会显得捉襟见肘，因为这个set会吃掉很大一部分常驻内存，不利于做持久化和大数据的增量爬取，而且由于集合太大，效率也是需要考虑的一方面。
### bloomfilter过滤器
&emsp;&emsp;bloomfilter可以很好的对大数据去重，其原理是通过多个哈希函数将网页的指纹映射到一段很长的bit位上(所以bit上都初始为0)，如下图，假设w是某个网页的指纹，那么它对应的3个哈希函数会将w运算成整数，然后在bit位上将该位置置为1，在做去重的时候，只需要对某个指纹同样的调用这个三个哈希函数，如果有其中一个位置是0，则说明这个指纹不存在可以插入，如果3个哈希函数判断得到的所有位置上的bit值都为1，则说明这个网页已经存在了。
![bloomfilter](https://upload-images.jianshu.io/upload_images/1803066-2a23dfc5462a0f4d.png?imageMogr2/auto-orient/)  
&emsp;&emsp;布隆过滤器只会判断不存在，绝不会多插入一条重复的数据，对于大数据，有忍耐很小部分丢失的情况下，布隆过滤器效率相当高。关于布隆过滤器的更多原理和误差可以看[这篇文章](https://cloud.tencent.com/developer/article/1084962)。在本项目中，引入了bloomfilter，它在redis中的类型为string，数据量大概在百万级别，利用了6个哈希函数，需要至少600W个位数的bit，所以开辟了一个长度为23位的bit段，2的23次方等于8388608，可以处理800W个网页的指纹，其在内存中所占用的内存才1MB。由此可见，利用bloomfilter既能够节省空间又能够提高去重效率，在有一定损失的情况下是一个很好的过滤器。
&emsp;&emsp;每次爬取完，这个去重的bit都会持久保存在redis中，所以下次重启爬虫的时候，可以不再重复爬取，这里就做到了持久化爬取。
### 过滤器参数设置
AppCommentsSpider/settings可以通过一下两字段分别设置hash函数的个数和bit的位数，这里默认为6个哈希函数和23个比特。
```
BLOOMFILTER_HASH_NUMBER = 6
BLOOMFILTER_BIT = 23
```
## 结语
&emsp;&emsp;上述网站都会不定期做相应的反爬虫处理，所以爬虫的代码也需要及时更新。反爬虫方面，本项目只做了随机user_agent和分布式爬取。单机器爬取时也可以适当做些限速处理。由于加入的bloomfilter，所以在spider中的scrapy.Request函数中要特别注意哪些需要dont_filter哪些不需要，比如贴吧爬虫，每一个next_page在下次爬取的时候都要获取，这里就不能设置dont_filter=True，但是每个帖子都要单独的指纹，为了防止下次爬取的时候重复爬取则不添加dont_filter字段，使用其默认值为False。
