# -*- coding: utf-8 -*-

import scrapy

from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.contrib.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.selector import Selector
import re
import json

from news_spider.items import NewsSpiderItem


class NewsSpider(CrawlSpider):
    name = "news"


    CRAWL_URLS = {
        'shehui': {
            'channels': ['shehui'],
            'ajax_url': 'http://temp.163.com/special/00804KVA/cm_{}.js',
            'ajax_urls': 'http://temp.163.com/special/00804KVA/cm_{}_0{}.js',
            'max': 1,
            'description': '普通频道，3个子频道：社会，国际，国内'
        },
        'guoji': {
            'channels': ['guoji'],
            'ajax_url': 'http://temp.163.com/special/00804KVA/cm_{}.js',
            'ajax_urls': 'http://temp.163.com/special/00804KVA/cm_{}_0{}.js',
            'max': 8,
            'description': '普通频道，3个子频道：社会，国际，国内'
        },
        'guonei': {
            'channels': ['guonei'],
            'ajax_url': 'http://temp.163.com/special/00804KVA/cm_{}.js',
            'ajax_urls': 'http://temp.163.com/special/00804KVA/cm_{}_0{}.js',
            'max': 8,
            'description': '普通频道，3个子频道：社会，国际，国内'
        },
        'sports': {
            'channels': ['index', 'allsports', 'cba', 'nba', 'china', 'world'],
            'ajax_url': 'http://sports.163.com/special/000587PR/newsdata_n_{}.js',
            'ajax_urls': 'http://sports.163.com/special/000587PR/newsdata_n_{}_0{}.js',
            'extra_urls': ['http://sports.163.com/special/000587PR/newsdata_n_index_10.js'],
            'max': 5,
            'description': '体育频道，6个子频道：首页，热点，CBA，NBA，国足，世界足球'
        },
        'ent': {
            'channels': ['index', 'star', 'movie', 'tv', 'show', 'music'],
            'ajax_url': 'http://ent.163.com/special/000380VU/newsdata_{}.js',
            'ajax_urls': 'http://ent.163.com/special/000380VU/newsdata_{}_0{}.js',
            'max': 8,
            'description': '娱乐频道，6个子频道：首页，明星，电影，电视剧，综艺，音乐'
        },
        'money': {
            'channels': ['index', 'stock', 'chanjing', 'finance', 'fund', 'licai', 'biz'],
            'ajax_url': 'http://money.163.com/special/002557S5/newsdata_idx_{}.js',
            'ajax_urls': 'http://money.163.com/special/002557S5/newsdata_idx_{}_0{}.js',
            'max': 8,
            'description': '财经频道，7个子频道：首页，股票，产经，金融，基金，理财，商业'
        },
        'tech': {
            'channels': ['datalist'],
            'ajax_url': 'http://tech.163.com/special/00097UHL/tech_{}.js',
            'ajax_urls': 'http://tech.163.com/special/00097UHL/tech_{}_0{}.js',
            'max': 3,
            'description': '科技频道'
        },
        'lady': {
            'channels': ['fashion', 'sense', 'travel', 'art', 'edu', 'baby'],
            'ajax_url': 'http://lady.163.com/special/00264OOD/data_nd_{}.js',
            'ajax_urls': 'http://lady.163.com/special/00264OOD/data_nd_{}_0{}.js',
            'max': 5,
            'description': '女性频道，6个子频道：时尚，情爱，旅游，艺术，教育，亲子'
        },
        'edu': {
            'channels': ['hot', 'liuxue', 'yimin', 'en', 'daxue', 'gaokao'],
            'ajax_url': 'http://edu.163.com/special/002987KB/newsdata_edu_{}.js',
            'ajax_urls': 'http://edu.163.com/special/002987KB/newsdata_edu_{}_0{}.js',
            'max': 3,
            'description': '教育频道，6个子频道：热点，留学，移民，外语，校园，高考'
        },
    }

    start_urls = []

    # http://news.163.com/17/0823/20/CSI5PH3Q000189FH.html
    url_pattern = r'((https|http)://(\w+)\.163\.com)/(\d{2})/(\d{4})/\d+/(\w+)\.html'

    def __init__(self, *a, **kw):
        super(NewsSpider, self).__init__(*a, **kw)
        urls = []
        for k, v in self.CRAWL_URLS.items():
            for c in v['channels']:
                urls.append(v['ajax_url'].format(c))
                for i in range(2, v['max'] + 1):
                    urls.append(v['ajax_urls'].format(c, i))
        self.start_urls.extend(urls)
        # self.start_urls = ['http://temp.163.com/special/00804KVA/cm_guoji_02.js']
                


    def parse_news(self, response):
        if response.status != 200:
            return
        if response.text.startswith('<script>setTimeout'):
            return

        url = response.url
        title = response.xpath("//h1/text()").extract()[0]

        item = NewsSpiderItem()
        item['data'] = {
            'title': title,
            'source': 'netease',
            'url': url,
            'favicon': 'https://news.163.com/favicon.ico',
            'content': '\n'.join(response.xpath('//*[@id="endText"]/p/text()').extract()).strip()
        }
        time_text = response.xpath('//div[@class="post_time_source"]/text()')
        if time_text:
            time = time_text.extract_first().split()[0] + ' ' + time_text.extract_first().split()[1]
            item['data']['time'] = time
        source_text = response.xpath('//*[@id="endText"]/div[2]/span[1]/text()')
        if source_text:
            item['data']['ep_source'] = source_text.extract_first().split('：')[1].strip()

        yield item

    def parse(self, response):
        print(response.url)
        text = response.body.decode('gbk').replace('data_callback(', '')[:-1]
        j = json.loads(text)

        for news in j:
            url = news['docurl']
            if re.match(self.url_pattern, url):
                yield scrapy.Request(url, meta={'origin': news}, callback=self.parse_news)