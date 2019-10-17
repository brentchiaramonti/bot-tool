# -*- coding: utf-8 -*-

import pytest
import vcr
import requests

import scrapy

from botbot import botbot
from botbot.spiders import spider

import pdb

@pytest.fixture
def response_B1():
    url = 'https://www.toothfixer.net/'
    website = botbot.Website(url)
    bot_bot_spider = spider.BotBotSpider(website=website)
    with vcr.use_cassette('tests/cassettes/response_B1.yaml'):
        response = requests.get(url)
    scrapy_response = scrapy.http.TextResponse(body=response.content, url=url)
    return bot_bot_spider, scrapy_response

@pytest.fixture
def response_O1():
    url = 'https://www.lynchdentalcenter.com/'
    website = botbot.Website(url)
    bot_bot_spider = spider.BotBotSpider(website=website)
    with vcr.use_cassette('tests/cassettes/response_O1.yaml'):
        response = requests.get(url)
    scrapy_response = scrapy.http.TextResponse(body=response.content, url=url)
    return bot_bot_spider, scrapy_response

@pytest.fixture
def response_T1():
    url ='https://www.chinohillscounseling.com/'
    website = botbot.Website(url)
    bot_bot_spider = spider.BotBotSpider(website=website)
    with vcr.use_cassette('tests/cassettes/response_T1.yaml'):
        response = requests.get(url)
    scrapy_response = scrapy.http.TextResponse(body=response.content, url=url)
    return bot_bot_spider, scrapy_response
