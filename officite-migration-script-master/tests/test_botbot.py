#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Unit tests for botbot.py. Uses the pytest suite.
"""

from botbot import botbot
from botbot.spiders import spider
from botbot import pipelines

import pytest
import pickle
import pdb

##############
# Unit Tests #
##############

class TestBotBot():
    """General unit test class for global functions in botbot.py.
    """
    pass

class TestWebsite():
    """Unit tests for the Website class in botbot.py
    """
    def test_extract_domain(self):
        # Case 1
        site_1 = botbot.Website("http://www2.example.com/blog/2017/04/21/blog-post.cfm?beep=boop&query=test%20")
        assert site_1.extract_domain() == "example.com"
        # Case 2
        site_2 = botbot.Website("ftp://doctor-tooth.co.uk/8EW.html?a=1234")
        assert site_2.extract_domain() == "doctor-tooth.co.uk"
        # Case 3
        site_3 = botbot.Website("swelldoc.com")
        assert site_3.extract_domain() == "swelldoc.com"
        # Case 4
        site_4 = botbot.Website("info@doctorallsunday.com")
        assert site_4.extract_domain() == "doctorallsunday.com"

class TestBotBotSpider():
    """Unit tests for the BotBotSpider class in botbot/spiders/spider.py
    """
    def test_parse_home(self):
        pass
    def test_identify_brand(self, response_B1, response_O1, response_T1):
        # Case 1: A known Baystone Media legacy website.
        bot_bot_spider = response_B1[0]
        scrapy_response = response_B1[1]
        bot_bot_spider.identify_brand(scrapy_response)
        assert bot_bot_spider.website.brand == 'B'
        # Case 2: A known Officite legacy website.
        bot_bot_spider = response_O1[0]
        scrapy_response = response_O1[1]
        bot_bot_spider.identify_brand(scrapy_response)
        assert bot_bot_spider.website.brand == 'O'
        # Case 3: A known TherapySites legacy website.
        bot_bot_spider = response_T1[0]
        scrapy_response = response_T1[1]
        bot_bot_spider.identify_brand(scrapy_response)
        assert bot_bot_spider.website.brand == 'T'
    
    #def test_parse_home_B(self):
    #    pass

class TestBotBotPipeline():
   """Unit tests for the BotBotPipeline class in botbot/pipelines.py
   """
   #def test_post_navigation(self, response_B1, reponse_O1, response_T1):
   #    # Case 1: Baystone Media legacy website navigation.
   #    bot_bot_spider = response_B1[0]
   #    scrapy_response = response_B1[1]
   #    bot_bot_spider.parse_home_B(scrapy_reponse)
   #
   #    # Case 2: Officite legacy website navigation.
   #    # Case 3: TherapySites Media legacy website navigation.
   #
   #
   #
