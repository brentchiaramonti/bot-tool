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
import wordninja
from spiders import spider
from scrapy.settings import Settings
# END: Redundant imports for Pyinstaller distribution

import tldextract
import wx
from gooey import Gooey
from gooey.gui.util import wx_util
from gooey.gui.components.header import FrameHeader

import webbrowser
from argparse import ArgumentParser
from oauthlib.common import generate_token
import urllib.parse
import time
import logging
import pdb


###########
# Globals #
###########

UNICODE_ASCII_CHARACTER_SET = ('abcdefghijklmnopqrstuvwxyz'
                               'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                               '0123456789')
PAD_SIZE = 10

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

def _new_layoutComponent(self):
    self.SetBackgroundColour(self.buildSpec['header_bg_color'])
    self.SetSize((30, self.buildSpec['header_height']))
    self.SetMinSize((120, 220))

    self._header = wx_util.h1(self, label=self.buildSpec['program_name'])
    self._subheader = wx.StaticText(self, label=self.buildSpec['program_description'])

    images = self.buildSpec['images']
    targetHeight = self.buildSpec['header_height'] - 10
    self.settings_img = self._load_image(images['configIcon'], targetHeight)
    self.running_img = self._load_image(images['runningIcon'], targetHeight)
    self.check_mark = self._load_image(images['successIcon'], targetHeight)
    self.error_symbol = self._load_image(images['errorIcon'], targetHeight)

    self.images = [
        self.settings_img,
        self.running_img,
        self.check_mark,
        self.error_symbol
    ]

    vsizer = wx.BoxSizer(wx.VERTICAL)
    sizer = wx.BoxSizer(wx.HORIZONTAL)
    headings_sizer = self.build_heading_sizer()
    sizer.Add(headings_sizer, 1,
              wx.ALIGN_LEFT | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND | wx.LEFT,
              PAD_SIZE)
    sizer.Add(self.settings_img, 0, wx.ALIGN_RIGHT | wx.EXPAND | wx.RIGHT, PAD_SIZE)
    sizer.Add(self.running_img, 0, wx.ALIGN_RIGHT | wx.EXPAND | wx.RIGHT, PAD_SIZE)
    sizer.Add(self.check_mark, 0, wx.ALIGN_RIGHT | wx.EXPAND | wx.RIGHT, PAD_SIZE)
    sizer.Add(self.error_symbol, 0, wx.ALIGN_RIGHT | wx.EXPAND | wx.RIGHT, PAD_SIZE)
    self.running_img.Hide()
    self.check_mark.Hide()
    self.error_symbol.Hide()
    vsizer.Add(sizer, 0, wx.EXPAND)
    self.SetSizer(vsizer)


def _new_build_heading_sizer(self):
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.AddStretchSpacer(1)
    sizer.Add(self._header, 0)
    sizer.Add(self._subheader, 0)

    self._button_log_in_B = wx.Button(self, wx.ID_ANY, 'Log In - Baystone')
    self._button_log_in_B.SetBackgroundColour(wx.Colour(100, 150, 250))
    self._button_log_in_B.Bind(wx.EVT_BUTTON, callback_button_log_in_B)
    sizer.Add(self._button_log_in_B, 0)

    self._button_log_in_O = wx.Button(self, wx.ID_ANY, 'Log In - Officite')
    self._button_log_in_O.SetBackgroundColour(wx.Colour(100, 200, 90))
    self._button_log_in_O.Bind(wx.EVT_BUTTON, callback_button_log_in_O)
    sizer.Add(self._button_log_in_O, 0)

    self._button_log_in_T = wx.Button(self, wx.ID_ANY, 'Log In - TherapySites')
    self._button_log_in_T.SetBackgroundColour(wx.Colour(115, 100, 250))
    self._button_log_in_T.Bind(wx.EVT_BUTTON, callback_button_log_in_T)
    sizer.Add(self._button_log_in_T, 0)



    self._button_log_out_B = wx.Button(self, wx.ID_ANY, 'Log Out - Baystone')
    self._button_log_out_B.SetBackgroundColour(wx.Colour(225, 90, 70))
    self._button_log_out_B.Bind(wx.EVT_BUTTON, on_button_log_out_B)
    sizer.Add(self._button_log_out_B, 0)

    self._button_log_out_O = wx.Button(self, wx.ID_ANY, 'Log Out - Officite')
    self._button_log_out_O.SetBackgroundColour(wx.Colour(225, 90, 70))
    self._button_log_out_O.Bind(wx.EVT_BUTTON, on_button_log_out_O)
    sizer.Add(self._button_log_out_O, 0)

    self._button_log_out_T = wx.Button(self, wx.ID_ANY, 'Log Out - TherapySites')
    self._button_log_out_T.SetBackgroundColour(wx.Colour(225, 90, 70))
    self._button_log_out_T.Bind(wx.EVT_BUTTON, on_button_log_out_T)
    sizer.Add(self._button_log_out_T, 0)


    sizer.AddStretchSpacer(1)
    return sizer

def create_log_in_link_B():
    authorization_url = 'https://login.onlinechiro.com/auth'
    params = {'client_id':'smbportalibc', 'redirect_uri':'https://portaladmin.onlinechiro.com/site/login', 'response_type':'token', 'scope':'openid brand', 'state':generate_token(length=30, chars=UNICODE_ASCII_CHARACTER_SET)}
    # Authenication
    params = urllib.parse.urlencode(params)
    parts = urllib.parse.SplitResult(scheme='https', netloc='login.onlinechiro.com', path='/auth', query=params, fragment='')
    log_in_url = urllib.parse.urlunsplit(parts)
    return log_in_url

def create_log_in_link_O():
    authorization_url = 'https://login.officite.com/auth'
    params = {'client_id':'smbportalibc', 'redirect_uri':'https://secure.officite.com/site/login', 'response_type':'token', 'scope':'openid brand', 'state':generate_token(length=30, chars=UNICODE_ASCII_CHARACTER_SET)}
    # Authenication
    params = urllib.parse.urlencode(params)
    parts = urllib.parse.SplitResult(scheme='https', netloc='login.officite.com', path='/auth', query=params, fragment='')
    log_in_url = urllib.parse.urlunsplit(parts)
    return log_in_url

def create_log_in_link_T():
    authorization_url = 'https://login.therapysites.com/auth'
    params = {'client_id':'smbportalibc', 'redirect_uri':'https://portaladmin.therapysites.com/site/login', 'response_type':'token', 'scope':'openid brand', 'state':generate_token(length=30, chars=UNICODE_ASCII_CHARACTER_SET)}
    # Authenication
    params = urllib.parse.urlencode(params)
    parts = urllib.parse.SplitResult(scheme='https', netloc='login.therapysites.com', path='/auth', query=params, fragment='')
    log_in_url = urllib.parse.urlunsplit(parts)
    return log_in_url

def callback_button_log_in_B(event, url=create_log_in_link_B()):
    return on_button_log_in(event, url)

def callback_button_log_in_O(event, url=create_log_in_link_O()):
    return on_button_log_in(event, url)

def callback_button_log_in_T(event, url=create_log_in_link_T()):
    return on_button_log_in(event, url)

def on_button_log_in(event, url):
    webbrowser.open(url, new=0, autoraise=True)

def on_button_log_out_B(event):
    webbrowser.open('https://portaladmin.onlinechiro.com/site/logout', new=0, autoraise=True)

def on_button_log_out_O(event):
    webbrowser.open('https://secure.officite.com/site/logout', new=0, autoraise=True)

def on_button_log_out_T(event):
    webbrowser.open('https://portaladmin.therapysites.com/site/logout', new=0, autoraise=True)

########
# Main #
########


# Monkey-patch the header of Gooey to create a custom button
FrameHeader.build_heading_sizer = _new_build_heading_sizer
FrameHeader.layoutComponent = _new_layoutComponent

# Gooey Options
@Gooey(advanced=True,
       program_name='B.O.T. Bot GUI',
       program_description='Log in using the button below.',
       default_size=(800, 600),
       header_height = 150,
       required_cols=1,
       optional_cols=1,
       disable_progress_bar_animation=True,
       monospace_display=True)
def main():

    parser = ArgumentParser()

    parser.add_argument(
        'redirect_url',
        metavar='Redirect URL',
        help='Log in using the button above. Copy-and-paste the URL here after logging in.',
        type=str)

    parser.add_argument(
        'website',
        metavar='Home Page',
        help='The home page of the legacy website. Include the protocol (\'http\' or \'https\').',
        type=str)

    parser.add_argument(
        'site_id',
        metavar='Site ID',
        help='The site ID number of the new, SMB Web Manager website.',
        type=str)

    parser.add_argument(
        'site_id_confirm',
        metavar='Site ID Confirmation',
        help='Please re-enter the site ID number. Make sure this is correct before proceeding!',
        type=str)

    parser.add_argument(
        '--legacy_id',
        metavar='Officite Legacy Website ID',
        help='Please enter the website ID number of the legacy website.',
        type=str,
        default='',
        required=False
        )


    args = parser.parse_args()


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


    redirect_url = args.redirect_url


    if args.site_id != args.site_id_confirm:
        print('ERROR! Site ID numbers do not match. The program will now cease execution.', flush=True)
        exit()
    else:
        pass

    # Parse the redirect_url for the access code
    redirect_split = urllib.parse.urlsplit(redirect_url)
    try:
        access_token = urllib.parse.parse_qs(redirect_split.fragment)['access_token'][0]
        print('Access granted.', flush=True)
    except Exception:
        print('ERROR! Invalid inputs! The program will now cease execution.', flush=True)
        exit()

    website = args.website

    site_id = args.site_id

    legacy_id = args.legacy_id


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
