#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""A legacy website scraper for Baystone Media, Officite, and TherapySites.

A legacy-website-specific website scraper for Baystone Media, 0fficite, and TherapySites.
The script crawls legacy websites. It then migrates data to portal accounts via the Web Manager API.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html
"""

###########
# Imports #
###########

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


# BEGIN: Redundant imports for Pyinstaller distribution
# This is because Pyinstaller only imports the bare minimum from this file.
# The spider.py file is not imported here; so Pyinstaller doesn't know about it
# nor its imports. It is necessary to import them here so Pyinstaller can see it.
# This applies to only 3rd party modules--not those built into Python.
# See the build.spec file for Pyinstaller Windows and MacOS builds.
# Command used to build the program with Pyinstaller:
# pyinstaller build.spec
# Also using hook-scrapy.py to take care of the majority of import errors.
import bs4
import slugify

from spiders import spider
from scrapy.settings import Settings
# END: Redundant imports for Pyinstaller distribution

import tldextract
from oauthlib.common import generate_token
import urllib.parse
import time
import logging
import pdb
import wordninja
###########
# Globals #
###########

UNICODE_ASCII_CHARACTER_SET = ('abcdefghijklmnopqrstuvwxyz'
                               'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                               '0123456789')


###########
# Classes #
###########

class Website():
    """A legacy website given by the user.
    """
    def __init__(self, url):
        self.url = url
        self.domain_name = self.extract_domain()
        self.brand = ''
        self.main_content_selector = ''

    def extract_domain(self):
        """Returns only the domain name (secondary and top-level) of a URL.
        """
        extraction = tldextract.extract(self.url)
        domain_name = extraction.domain + "." + extraction.suffix
        return domain_name


#############
# Functions #
#############

########
# Main #
########

def main():
    tui_welcome = """

                 ____   ____ _______   ____        _
                |  _ \ / __ \__   __| |  _ \      | |
                | |_) | |  | | | |    | |_) | ___ | |_
                |  _ <| |  | | | |    |  _ < / _ \| __|
                | |_) | |__| | | |_   | |_) | (_) | |_
                |____(_)____(_)|_(_)  |____/ \___/ \__|

v1.0                                                  (c) Internet Brands
==========================================================================
                              WELCOME!
==========================================================================
"""
    tui_seperator = """
==========================================================================
    """
    print(tui_welcome, flush=True)


    authorization_url = 'https://login.officite.com/auth'
    params = {'client_id':'smbportalibc', 'redirect_uri':'https://secure.officite.com/site/selectClient', 'response_type':'token', 'scope':'openid brand', 'state':generate_token(length=30, chars=UNICODE_ASCII_CHARACTER_SET)}

    # Authenication
    params = urllib.parse.urlencode(params)
    parts = urllib.parse.SplitResult(scheme='https', netloc='login.officite.com', path='/auth', query=params, fragment='')
    log_in_url = urllib.parse.urlunsplit(parts)
    print('In order to continue, you must authorize this program to access the portal.',
          'To do this, copy and paste the following link and log into the portal:',
          '\n\n'
    )
    print(log_in_url)
    print('\n\n')
    redirect_url = input('After logging in, copy and paste the URL in your web browser here:\n\n')
    print('\n\n')

    # Parse the redirect_url for the access code

    redirect_split = urllib.parse.urlsplit(redirect_url)
    try:
         access_token = urllib.parse.parse_qs(redirect_split.fragment)['access_token'][0]
         print('Access granted.')
    except Exception:
         print('ERROR! Unable to acquire access to the portal from the URL you provided.',
         'The program will now exit.')
         time.sleep(7)
         exit()


    website = input('Please provide the URL of a website to scrape: ')

    print('\n\n')

    site_id = input('Please give the ID number of the website: ')

    print('\n\n')

    legacy_id = input('Please give the legacy website ID number of the site: ')


    logger = logging.getLogger()
    logging.basicConfig(filename='log_dev.txt', filemode='w', level=logging.DEBUG)
    logger_friendly = logging.getLogger('logger_friendly')
    logger_friendly_handler = logging.handlers.RotatingFileHandler('log_user.txt', mode='w')
    logger_friendly_formatter= logging.Formatter('%(levelname)s: %(message)s')
    logger_friendly_handler.setFormatter(logger_friendly_formatter)
    logger_friendly.addHandler(logger_friendly_handler)


    logger_friendly.info('BOT Bot Started')

    # Old way of getting the project settings. This was replaced to make the program
    # easier to distribute with Pyinstaller. Keeping here for documentation purposes.
    #process = CrawlerProcess(get_project_settings())
    #process.crawl('botbot', website=Website(website), access_token=access_token, site_id=site_id)

    # New way of getting project settings
    settings = Settings()
    settings.setmodule('settings', priority='project')
    process = CrawlerProcess(settings)
    # Passing the spider class explictly for Pyinstaller; when Scrapy attempts to
    # 'look it up' using the spider's name, it comes up with an error as Scrapy attempts
    # to walk through modules in the Pyinstaller executable. Passing the spider class
    # prevents this.
    process.crawl(spider.BotBotSpider, website=Website(website), access_token=access_token, site_id=site_id, legacy_id=legacy_id)
    process.start() # the script will block here until the crawling is finished

    logger_friendly.info('BOT Bot Ended')


if __name__ == "__main__":
    main()
