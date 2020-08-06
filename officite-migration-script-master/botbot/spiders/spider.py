# -*- coding: utf-8 -*-

import scrapy

import items
from scrapy.loader import ItemLoader

from bs4 import BeautifulSoup, SoupStrainer
from slugify import slugify


import urllib.parse
from urllib.parse import urlparse
import json
import re
# from unidecode import unidecode # no longer used
import logging
import pdb
import wordninja

logger_friendly = logging.getLogger('logger_friendly')
logger_friendly.addHandler(logging.NullHandler())

class BotBotSpider(scrapy.Spider):
    """Website spider

    The instance of this class determines whats content to scrape based on the
    website given. Takes a Website object through a keyword argument which by
    default creates an attribute for the spider.
    """
    name = 'botbot'

    def __init__(self, website=None, access_token=None, site_id=None, legacy_id=None, *args, **kwargs):
        """Initializes the spider with a Website object.
        """
        super().__init__(*args, **kwargs)
        self.website = website
        self.access_token = access_token
        self.site_id = site_id
        self.legacy_id = legacy_id
        self.editor_url = '' # Used for changing file links to their Media Manager path
        self.legacy_data = '' # Set later. Holds Officite legacy website JSON data.
        self.mapping_dict = {} # Used to keep track of pages from legacy to smbwebmgr
        self.mapping_dict_titles = {}
        self.start_urls = [website.url]

    #############################
    # Start URL Parsing Methods #
    #############################

    def start_requests(self):
        yield self.get_editor_url(self.access_token, self.site_id)

    #def parse_start_url(self, response):
        #"""Requests the url given to the BotBotSpider object.
        #This url should be the home page of the website. Once the response
        #is received, it is actually parsed by parse_home.
        #"""
        #return self.parse_home(response)

    def parse_home(self, response):
        """Parses the home page for data to guide the rest of the crawl.
        """
        print('Got the home page.', flush=True)
        logger_friendly.info('Got the home page.')

        self.identify_brand(response)
    
        if self.website.brand == 'B':
            return self.parse_home_B(response)
        elif self.website.brand == 'O':
            return self.parse_home_O(response)
        elif self.website.brand == 'T':
            return self.parse_home_T(response)
        elif self.website.brand == 'W':
            return self.parse_home_W(response)
        else:
            return self.parse_home_X(response)

    def identify_brand(self, response):
        """Identifies the brand a legacy website belongs to.
        """


        if response.css('.columnsContent'):
            self.website.brand = 'B'
            self.website.main_content_selector = '.columnsContent'
            print('Identified a Baystone Media legacy site.', flush=True)
            logger_friendly.info('Identified a Baystone Media legacy site.')
        elif response.css('#slot-main'):
            self.website.brand = 'O'
            self.website.main_content_selector = '#slot-main'
            print('Identified an Officite legacy site.', flush=True)
            logger_friendly.info('Identified an Officite legacy site.')
        elif response.css('#content'):
            self.website.brand = 'T'
            self.website.main_content_selector = '#content'
            print('Identified a TherapySites legacy site.', flush=True)
            logger_friendly.info('Identified a TherapySites legacy site.')
        elif response.css('.editable__container--inner'):
            self.website.brand = 'W'
            self.website.main_content_selector = '.wrap__page-content--inner'
            print('Identified a Webmanager website', flush=True)
            logger_friendly.info('Identified a Webmanager website')
        else:
            self.website.brand = 'X'
            logger_friendly.info('Website identity unknown.')

    ##################################
    # Brand-Specific Parsing Methods #
    ##################################


    def parse_home_W(self, response):

        menu_scrapy_item = self.parse_navigation('#navigation_header > ul > li', \
                            response)
        menu = menu_scrapy_item['menu']

        # Configure the navigation component on smbwebmgr
        logger_friendly.info('Configuring the navigaton component on smbwebmgr.')
        yield self.put_navigation(menu_scrapy_item, 'navigation_header', self.access_token, self.site_id)
        yield self.put_navigation(menu_scrapy_item, 'navigation_body', self.access_token, self.site_id)
        yield self.put_navigation(menu_scrapy_item, 'partial_nav', self.access_token, self.site_id)

        menu_all_urls = self.generate_values(menu, 'url')

        print('Scraping files found in menu links ...', flush=True)
        logger_friendly.info('Scraping files found in menu links ...')
        # Download any internal links to files in the menu
        logger_friendly.info('The spider will now upload files in menu links to smbwebmgr.')
        yield from self.parse_menu_files(menu_all_urls)

        print('Scraping legacy stylesheets ...')
        logger_friendly.info('Scraping legacy stylesheets ...')
        # Upload the legacy stylesheet to smbwebmgr
        yield from self.parse_stylesheets(['link[href*="custom.css"]'], response)


        # Create a dictionary to serve as a mapping of legacy urls
        # to their new counterparts. This will help for 301 redirects, and
        # it will help to possibly avoid creating unnecessary new pages for
        # internal links for which a menu item already exists.
        mapping_dict = self.map_urls(menu, 'url', 'url_slug')
        self.mapping_dict = mapping_dict # To keep track of URLs
        mapping_dict_titles = self.map_urls(menu, 'url', 'title')
        self.mapping_dict_titles = mapping_dict_titles # To keep track of URLs

        print('Creating 301 redirects for menu links ...', flush=True)
        logger_friendly.info('Creating 301 redirects for menu links ...')
        # Create 301 redirects for each pair in the URL mapping dict
        yield from self.create_redirects(mapping_dict)

        # Try to look for a logo; if found, scrape and migrate.
        print('Scraping the logo  ...', flush=True)
        logger_friendly.info('Scraping the logo ...')


        # Get image
        if response.css('.logo__image'):
            logo_src = response.css('.logo__image').xpath('@src').extract_first()

        else:
            logo_src = ''



        if 'cdcssl.ibsrv.net' in logo_src: 
            if self.website.url.endswith('/'):
                logo_src = self.website.url + 'storage/app/media/' + logo_src.split('/')[-1]
            else:
                logo_src = self.website.url + '/storage/app/media/' + logo_src.split('/')[-1]


        # Configure the logo component
        yield from self.parse_logo(logo_src=logo_src)


        print('Scraping each web page found in the menu ..', flush=True)
        logger_friendly.info('Scraping each web page found in the menu ...')
        # Get all URLs in the menu
        menu_all_urls = self.generate_values(menu, 'url')
    

        # Gather all links for scraping pages from the menu
        for url in menu_all_urls:

            url = self.get_http(self.website.url) + url

            if url != '#':
                if self.check_if_internal(url):
                    if not self.check_if_file(url):
                      if self.check_if_relative(url):
                            url = self.make_absolute(url)
                      else:
                          pass
                      # Extra check to ensure the domain name in the url is lowercase
    
                      if 'articles/' in url or 'articles_dear_doctor/' in url:
                        continue
                      else:
                        pass

                      yield scrapy.Request(url, callback=self.parse_page)
                    else:
                        continue
                else:
                    continue
            else:
                continue
    
    
        print('Scraping the home page ..', flush=True)
        logger_friendly.info('Scraping the home page ...')
        # Process the home page using the generalized parsing method
        yield from self.parse_page(response)


    def parse_home_B(self, response):
        """Parses Baystone home pages to extract the menu structure and links.
        """
        print('Scraping the menu ...', flush=True)
        logger_friendly.info('Scraping the menu ...')
        # Traverse the menu tree
        menu_scrapy_item = self.parse_navigation('#mainMenu > li:not(.sep)', \
                           response)
        menu = menu_scrapy_item['menu']
    
    
        # Configure the navigation component on smbwebmgr
        logger_friendly.info('Configuring the navigaton component on smbwebmgr.')
        yield self.put_navigation(menu_scrapy_item, 'navigation_header', self.access_token, self.site_id)
        yield self.put_navigation(menu_scrapy_item, 'navigation_body', self.access_token, self.site_id)
        yield self.put_navigation(menu_scrapy_item, 'partial_nav', self.access_token, self.site_id)
    
    
        # Get all URLs in the menu
        menu_all_urls = self.generate_values(menu, 'url')
    
    
        print('Scraping files found in menu links ...', flush=True)
        logger_friendly.info('Scraping files found in menu links ...')
        # Download any internal links to files in the menu
        logger_friendly.info('The spider will now upload files in menu links to smbwebmgr.')
        yield from self.parse_menu_files(menu_all_urls)
    
    
        print('Scraping legacy stylesheets ...')
        logger_friendly.info('Scraping legacy stylesheets ...')
        # Upload the legacy stylesheet to smbwebmgr
        yield from self.parse_stylesheets(['link[href*="global.css"]'], response)
    
    
        # Create a dictionary to serve as a mapping of legacy urls
        # to their new counterparts. This will help for 301 redirects, and
        # it will help to possibly avoid creating unnecessary new pages for
        # internal links for which a menu item already exists.
        mapping_dict = self.map_urls(menu, 'url', 'url_slug')
        self.mapping_dict = mapping_dict # To keep track of URLs
        mapping_dict_titles = self.map_urls(menu, 'url', 'title')
        self.mapping_dict_titles = mapping_dict_titles # To keep track of URLs
    
    
    
        print('Creating 301 redirects for menu links ...', flush=True)
        logger_friendly.info('Creating 301 redirects for menu links ...')
        # Create 301 redirects for each pair in the URL mapping dict
        yield from self.create_redirects(mapping_dict)
    
    
        # Try to look for a logo; if found, scrape and migrate.
        print('Scraping the logo  ...', flush=True)
        logger_friendly.info('Scraping the logo ...')
        # Get image
        if response.css('.headerPkg img'):
            logo_src = response.css('.headerPkg img').xpath('@src').extract_first()
        else:
            logo_src = ''
        # Configure the logo component
        yield from self.parse_logo(logo_src=logo_src)
    
    
        print('Scraping each web page found in the menu ..', flush=True)
        logger_friendly.info('Scraping each web page found in the menu ...')
        # Get all URLs in the menu
        menu_all_urls = self.generate_values(menu, 'url')


        # Gather all links for scraping pages from the menu
        for url in menu_all_urls:
            if url != '#':
                if self.check_if_internal(url):
                    if not self.check_if_file(url):
                      if self.check_if_relative(url):
                            url = self.make_absolute(url)
                      else:
                          pass
                      # Extra check to ensure the domain name in the url is lowercase
    
                      yield scrapy.Request(url, callback=self.parse_page)
                    else:
                        continue
                else:
                    continue
            else:
                continue
    
    
        print('Scraping the home page ..', flush=True)
        logger_friendly.info('Scraping the home page ...')
        # Process the home page using the generalized parsing method
        yield from self.parse_page(response)
    
    
    
    
    

    def parse_home_O(self, response):
        """Parses Officite home pages to extract the menu structure and links.
        """
        print('Scraping the menu ...', flush=True)
        logger_friendly.info('Scraping the menu ...')
        # Traverse the menu tree
        menu_scrapy_item = self.parse_navigation('#slot-navigation > ul > li', \
                            response)
        menu = menu_scrapy_item['menu']
    
    
        # Configure the navigation component on smbwebmgr
        logger_friendly.info('Configuring the navigaton component on smbwebmgr.')
        yield self.put_navigation(menu_scrapy_item, 'navigation_header', self.access_token, self.site_id)
        yield self.put_navigation(menu_scrapy_item, 'navigation_body', self.access_token, self.site_id)
        yield self.put_navigation(menu_scrapy_item, 'partial_nav', self.access_token, self.site_id)
    
        # Get all URLs in the menu
        menu_all_urls = self.generate_values(menu, 'url')
    
    
        print('Scraping files found in menu links ...', flush=True)
        logger_friendly.info('Scraping files found in menu links ...')
        # Download any internal links to files in the menu
        logger_friendly.info('The spider will now upload files in menu links to smbwebmgr.')
        yield from self.parse_menu_files(menu_all_urls)
    
    
        print('Scraping legacy stylesheets ...', flush=True)
        logger_friendly.info('Scraping legacy stylesheets ...')
        # Upload the legacy stylesheet to smbwebmgr
        yield from self.parse_stylesheets(['link[href*="layout.css"]', \
                                            'link[href*="customer.css"]'], response)
    
    
        # Create a dictionary to serve as a mapping of legacy urls
        # to their new counterparts. This will help for 301 redirects, and
        # it will help to possibly avoid creating unnecessary new pages for
        # internal links for which a menu item already exists.
        mapping_dict = self.map_urls(menu, 'url', 'url_slug')
        self.mapping_dict = mapping_dict # To keep track of URLs
        mapping_dict_titles = self.map_urls(menu, 'url', 'title')
        self.mapping_dict_titles = mapping_dict_titles # To keep track of URLs
    
    
    
        print('Creating 301 redirects for menu links ...', flush=True)
        logger_friendly.info('Creating 301 redirects for menu links ...')
        # Create 301 redirects for each pair in the URL mapping dict
        yield from self.create_redirects(mapping_dict)
    
    
    
        # Try to look for a logo; if found, scrape and migrate.
        print('Scraping the logo  ...', flush=True)
        logger_friendly.info('Scraping the logo ...')
        # Get image
        if response.css('.logo-phone-wrapper-inner img'):
            logo_src = response.css('.logo-phone-wrapper-inner img').xpath('@src').extract_first()
        else:
            logo_src = ''
        # Configure the logo component
        yield from self.parse_logo(logo_src=logo_src)
    
    
        # Configure locations, hours, map, and social media components if legacy data is available.
        if self.legacy_id:
            print('Adding legacy locations, hours, latitude, longitude and social media ...', flush=True)
            logger_friendly.info('Adding legacy locations, hours, latitude, longitude and social media ...')
            yield from self.parse_locations_O(self.legacy_data)
            yield from self.parse_hours_O(self.legacy_data)
            yield from self.parse_socialmedia_O(self.legacy_data)
        else:
            pass
    
    
    
        # Scrape each web page in the menu.
        print('Scraping each web page found in the menu ...', flush=True)
        logger_friendly.info('Scraping each web page found in the menu ...')
        # Get all URLs in the menu
        menu_all_urls = self.generate_values(menu, 'url')
        # Gather all links for scraping pages from the menu
        for url in menu_all_urls:
            if url != '#':
                if self.check_if_internal(url):
                    if not self.check_if_file(url):
                        if self.check_if_relative(url):
                            url = self.make_absolute(url)
                        else:
                            pass
    
                        yield scrapy.Request(url, callback=self.parse_page)
                    else:
                        continue
                else:
                    continue
            else:
                continue
    
        print('Scraping the home page ..', flush=True)
        logger_friendly.info('Scraping the home page ...')
        # Process the home page using the generalized parsing method
        yield from self.parse_page(response)
    

    def parse_home_T(self, response):
        """Parses TherapySites home pages to extract the menu structure and links.
        """
        print('Scraping the menu ...', flush=True)
        logger_friendly.info('Scraping the menu ...')
        # Traverse the menu tree
        menu_scrapy_item = self.parse_navigation('#nav > li', \
                            response)
        menu = menu_scrapy_item['menu']
    
    
        # Configure the navigation component on smbwebmgr
        logger_friendly.info('Configuring the navigaton component on smbwebmgr.') 
        yield self.put_navigation(menu_scrapy_item, 'navigation_header', self.access_token, self.site_id)
        yield self.put_navigation(menu_scrapy_item, 'navigation_body', self.access_token, self.site_id)
        yield self.put_navigation(menu_scrapy_item, 'partial_nav', self.access_token, self.site_id)
    
    
        # Get all URLs in the menu
        menu_all_urls = self.generate_values(menu, 'url')
    
    
        print('Scraping files found in menu links ...', flush=True)
        logger_friendly.info('Scraping files found in menu links ...')
        # Download any internal links to files in the menu
        logger_friendly.info('The spider will now upload files in menu links to smbwebmgr.')
        yield from self.parse_menu_files(menu_all_urls)
    
    
        # TODO Scrape inline styles for TherapySites
        # All TherapySites custom CSS work is done inline. There is no
        # legacy stylesheet--just legacy <style> tags.
    
    
        # Create a dictionary to serve as a mapping of legacy urls
        # to their new counterparts. This will help for 301 redirects, and
        # it will help to possibly avoid creating unnecessary new pages for
        # internal links for which a menu item already exists.
        mapping_dict = self.map_urls(menu, 'url', 'url_slug')
        self.mapping_dict = mapping_dict # To keep track of URLs
        mapping_dict_titles = self.map_urls(menu, 'url', 'title')
        self.mapping_dict_titles = mapping_dict_titles # To keep track of URLs
    
    
    
        print('Creating 301 redirects for menu links ...', flush=True)
        logger_friendly.info('Creating 301 redirects for menu links ...')
        # Create 301 redirects for each pair in the URL mapping dict
        yield from self.create_redirects(mapping_dict)
    
    
        # Try to look for a logo; if found, scrape and migrate.
        print('Scraping the logo  ...', flush=True)
        logger_friendly.info('Scraping the logo ...')
        # Get title
        if response.css('.website-title'):
            title = response.css('.website-title')\
                    .xpath('descendant::text()[normalize-space()]').extract_first()
        else:
            title = ''
        # Get description
        if response.css('.website-subtitle'):
            description = response.css('.website-subtitle')\
                    .xpath('descendant::text()[normalize-space()]').extract_first()
        else:
            description = ''
        # Get image
        if response.css('#headerWrapper img'):
            logo_src = response.css('#headerWrapper img').xpath('@src').extract_first()
        else:
            logo_src = ''
        # Configure the logo component
        yield from self.parse_logo(title=title, description=description, logo_src=logo_src)
    
    
    
        print('Scraping each web page found in the menu ..', flush=True)
        logger_friendly.info('Scraping each web page found in the menu ...')
        # Get all URLs in the menu
        menu_all_urls = self.generate_values(menu, 'url')
        # Gather all links for scraping pages from the menu
        for url in menu_all_urls:
            if url != '#':
                if self.check_if_internal(url):
                    if not self.check_if_file(url):
                        if self.check_if_relative(url):
                            url = self.make_absolute(url)
                        else:
                            pass
                        yield scrapy.Request(url, callback=self.parse_page)
                    else:
                        continue
                else:
                    continue
            else:
                continue
    
    
        print('Scraping the home page ..', flush=True)
        logger_friendly.info('Scraping the home page ...')
        # Process the home page using the generalized parsing method
        yield from self.parse_page(response)

    def parse_home_X(self, response):
        """Parses the home page of an unidentified website.
        """
        pass

    #def parse_page_B(self, response):
    #    """Parses a Baystone Media legacy website web page.
    #    """
    #    pass

    #

    #

    #

    ###############################################
    # Methods that Operate on Links and Filenames #
    ###############################################

    def check_if_internal(self, link):
        """Return True if the given link is internal to the website being scraped.
    
        Links from subdomains of the client's domain name or company domain/subdomains
        are also marked as 'internal'.
        """
        parsed_link = urlparse(link)
        parsed_base_url = urlparse(self.website.url)


        # Check 'internal' link
        if parsed_link.netloc and (self.website.domain_name in parsed_link.netloc.lower() or \
            'baystonemedia.com' in parsed_link.netloc or \
            'officite.com' in parsed_link.netloc or \
            'therapysites.com' in parsed_link.netloc):
            return True
        # Mark as 'external'
        elif parsed_link.scheme and parsed_link.scheme not in ['http', 'https']:
            return False
        # Check if relative link (which must be interal)
        elif self.check_if_relative(link):
            return True
        # Else, link must be external
        else:
            return False

    def check_if_file(self, link):
        """Checks a URL for for common image and document file extensions.
        """
        # A more accurate method would be to make HEAD requests for each resource
        # and then check if the Content-Type header of the response to see if the
        # requested resource is a file. But, this method is does not require making
        # requests.
        extension_whitelist = ['png', 'jpeg', 'jpg', 'gif', 'tif', 'pdf', 'doc', \
            'docx', 'js', 'css', 'mp3', 'mp4', 'rtf']
        #parsed_link = urlparse(link) # removed need to use urlparse
        if '.' in link:
            filename = link.split('/')[-1]
            # Remove query parameters if the filename still has them.
            filename = filename.split('?')[0]
            filename = filename.split('&')[0]
            # A path could end in '/', but if it does it most likely not a file
            extension = filename.split('.')[-1]
            if extension.lower() in extension_whitelist:
                return True
            else:
                return False
        else:
            return False

    def get_filename(self, link):
        """Splits a URL to get the file name of a resource.
        """
        #parsed_link = urlparse(link) # removed need to use urllib
        filename = link.split('/')[-1]
        # Remove query parameters if the filename still has them.
        filename = filename.split('?')[0]
        filename = filename.split('&')[0]
        return filename

    def check_if_relative(self, link):
        """Return True if the given link is relative.
        """
        parsed_link = urlparse(link)
        if not parsed_link.netloc:
            return True
        else:
            return False

    def make_absolute(self, link):
        return urllib.parse.urljoin(self.website.url, link)

    @staticmethod
    def deny_links(href):
        """Filter function to deny links based on regex for Beautiful Soup.
        """
        return href and not (re.compile('library').search(href) or \
        re.compile('blog').search(href) or \
        re.compile('email-protection').search(href) or \
        re.compile('mailto:').search(href) or \
        re.compile('tel:').search(href) or \
        re.compile('captcha').search(href) or \
        re.compile('category').search(href))
    

    @staticmethod
    def get_lib_links(href):
        """Filter function to get legacy Officite library links.
        """
        return href and re.compile('library').search(href)
    

    def sanitize_filename(self, filename):
        """Sanitizes filenames strictly for use in uploading files for API calls.
        """
        # Replace all spaces with dashes
        filename = re.compile('\s+').sub('-', filename)
        # Replace muliple instances of underscores and dashes with dashes
        filename = re.compile('\_+').sub('-', filename)
        filename = re.compile('\-+').sub('-', filename)
        # Remove all 'non-friendly' characters
        filename = re.compile(r'[^a-zA-Z0-9\.\-]').sub('', filename)
        # Remove leading and trailing dashes
        if filename[0] == '-':
            filename = filename[1:]
        elif filename[-1] == '-':
            filename = filename[:-1]
        else:
            pass
        # Make the entire file name lowercase
        filename = filename.lower()
        return filename

    #################################
    # Methods that Operate on Menus #
    #################################

    def parse_external(self, response):
        """Gathers only the Content-Type of the response for an external link request.
        """
        pass

    def check_if_parent(self, selector):
        """Checks if a given selector has any children ul elements.
        """
        if selector.xpath('ul'):
            return 1
        else:
            return 0

    def traverse(self, selectors, menu, parent=None):
        """Traverses the menu tree using a depth-first search.
    
           This function is generalized to work on Baystone Media, Officite,
           and TherapySites legacy websites with the given level 1 li
           selectors. Works for menu structures using nested ul tags.
        """
        for selector in selectors:
            menu_item_loader = ItemLoader(items.MenuItem())
            url = selector.xpath('descendant::a/@href').extract_first()
            title = selector.xpath('descendant::text()[normalize-space()]') \
                            .extract_first()
            url_slug = '/' + slugify(title)
            menu_item_loader.item['url'] = url
            menu_item_loader.item['title'] = title
            menu_item_loader.item['url_slug'] = url_slug
            # Designate the parent of this menu item if there is one
            if parent:
                menu_item_loader.item['parent'] = parent
            else:
                pass
            # Check for children
            is_parent = self.check_if_parent(selector)
            if is_parent:
                menu_item_loader.item['is_parent'] = 1
                menu_item_loader.item['children'] = []
                menu_item_loader.load_item()
                menu.append(menu_item_loader.item)
                self.traverse(selector.xpath('ul/li'), menu_item_loader.item['children'], parent=url_slug)
            else:
                menu_item_loader.item['is_parent'] = 0
                menu_item_loader.item['children'] = []
                menu_item_loader.load_item()
                menu.append(menu_item_loader.item)
        return menu

    def generate_values(self, l, key):
        """Get all values of a key in a nested dictionary structure with lists.
    
        Recursive generator function to get all values of a specified key in
        a nested dictionary.
        """
        for d in l:
            if key in d:
                yield d[key]
            for i in d:
                if isinstance(d[i], list):
                    for j in self.generate_values(d[i], key):
                        yield j

    def menu_to_dict(self, menu_item_list, menu_dict):
        """Constructs a dictionary out of a Menu Scrapy item for smbwebmgr API calls.
        """
        home_page_seen = 0
        for menu_item in menu_item_list:
            menu_item_dict = {}
            # Check for a 'Home' or 'Welcome' page
            # Only let one through to be the home page.
            if menu_item['title'] in ['Home', 'Welcome'] and home_page_seen:
                continue
            else:
                home_page_seen = 1
            menu_item_dict['title'] = menu_item['title']
            # Check for no link, internal, file, or external
            if menu_item['url'] == '#':
                menu_item_dict['url'] = "#"
            elif self.check_if_internal(menu_item['url']):
                # Check if link to file
                if self.check_if_file(menu_item['url']):
                    filename = self.get_filename(menu_item['url'])
                    filename = self.sanitize_filename(filename)
                    media_manager_link = self.editor_url[:-15] + 'storage/app/media/' + \
                        filename
                    menu_item_dict['url'] = media_manager_link
                else:
                    if menu_item['title'] in ['Home', 'Welcome']:
                        menu_item_dict['url'] = '/'
                    else:
                        menu_item_dict['url'] = menu_item['url_slug']
            else:
                menu_item_dict['url'] = menu_item['url']
            menu_item_dict['newTab'] = '0'
            menu_item_dict['items'] = []
            if menu_item['children']:
                menu_dict['items'].append(menu_item_dict)
                self.menu_to_dict(menu_item['children'], menu_item_dict)
            else:
                menu_dict['items'].append(menu_item_dict)
        return menu_dict
    
    

    ##########################
    # Callbacks and Errbacks #
    ##########################

    def callback_editor_url(self, response):
        """Sets the editor_url attribute for the website to be used by other functions.
        """
        response_json = json.loads(response.body.decode('utf-8'))
        self.editor_url = response_json['sites'][0]['editor_url']
        # Make sure the protocol for the editor_url is set to 'https'
        self.editor_url = self.editor_url.replace('http', 'https')
        print('Found the website editor page for the given site ID.', flush=True)
        logger_friendly.info('Found the website editor page for the given site ID.')
        if self.legacy_id:
            return self.get_legacy_data(self.access_token, self.legacy_id)
        else:
            return scrapy.Request(self.website.url, callback=self.parse_home)

    def callback_legacy_data(self, response):
        """Sets JSON data for the legacy website to be used by other functions.
        """
        self.legacy_data = json.loads(response.body.decode('utf-8'))
        print('Communicated with legacy database. Got legacy website data.', flush=True)
        logger_friendly.info('Communicated with legacy database. Got legacy website data.')
        return scrapy.Request(self.website.url, callback=self.parse_home)

    def callback_navigation(self, response):
        pass

    def errback_navigation(self, failure):
        pass

    def callback_file(self, response):
        pass

    def errback_file(self, failure):
        pass

    def callback_css(self, response):
        pass

    def callback_redirect(self, response):
        pass

    def callback_page(self, failure):
        pass

    def errback_page(self, failure):
        pass

    def callback_logo(self, response):
        pass

    def callback_locations(self, response):
        pass

    def callback_maps(self, response):
        pass

    def errback_locations(self, failure):
        pass

    def callback_locations_O(self, response):
        pass

    def errback_locations_O(self, failure):
        pass

    def callback_hours_O(self, response):
        pass

    def errback_hours_O(self, failure):
        pass

    def callback_socialmedia_O(self, response):
        pass

    def errback_socialmedia_O(self, failure):
        pass

    #######################################
    # Methods that Call the SMBWEBMGR API #
    #######################################

    def get_editor_url(self, access_token, site_id):
        """GET the editor url for the site using the smbwebmgr API.
        """
        headers = {'Content-Type':'application/json', 'Authorization':'Bearer ' + access_token}
    
        return scrapy.Request('https://smbwebmgr.internetbrands.com/api/sites/' + site_id,\
                                method='GET', headers=headers, priority=1, callback=self.callback_editor_url)

    def get_legacy_data(self, access_token, legacy_id):
        """GET the legacy data for Officite SiteBuilder sites via the legacy API Han Liu had set up.
        """
        headers = {'Content-Type':'application/json', 'Authorization':'Bearer ' + access_token}
    
        return scrapy.Request('https://api.officite.com/api/v1/websiteData/' + legacy_id,\
                                method='GET', headers=headers, priority=1, callback=self.callback_legacy_data)

    def put_navigation(self, menu, component_alias, access_token, site_id):
        """PUT request to configure the navigation component in smbwebmgr.
    
        The navigation component only supports up to 3 menu nesting levels.
        """
        headers = {'Content-Type':'application/json', 'Authorization':'Bearer ' + access_token}
        body = {'name': component_alias, 'items': []}
        body = self.menu_to_dict(menu['menu'], body)
        body = json.dumps(body, sort_keys=True)
    
        return scrapy.Request('https://smbwebmgr.internetbrands.com/api/sites/' + site_id + \
        '/navigations/' + component_alias, method='PUT', headers=headers, body=body, \
        callback=self.callback_navigation, errback=self.errback_navigation)

    def post_file(self, url, sanitized_filename, access_token, site_id):
        """POST a file to smbwebmgr using its API.
    
        TODO The Scrapy DUPEFILTER_CLASS setting should prevent duplicate
        requests from being made for the same resource. Look into this ...
        """
        
        if("http" not in url):
            url = self.get_http(self.website.url) + url
        


        headers = {'Content-Type':'application/json', 'Authorization':'Bearer ' + access_token}
        body = {'url': url, 'filename':sanitized_filename}
        body = json.dumps(body, sort_keys=True)
    
        return scrapy.Request('https://smbwebmgr.internetbrands.com/api/sites/' + site_id + \
            '/files/', method='POST', headers=headers, body=body, callback=self.callback_file)

    def put_css(self, css_file_list, access_token, site_id):
        """PUT a CSS file to smbwebmgr using its API.
    
        TODO Open a JIRA to create an API endpoint so that CSS
        files are not served from the Media Manager.
        """



        headers = {'Content-Type':'application/json', 'Authorization':'Bearer ' + access_token}
        links_stylesheets = ""
        #for css_file in css_file_list:
        #    links_stylesheets += '<link rel="stylesheet" type="text/css" href="'\
        #        + self.editor_url[0:-15] + 'storage/app/media/' + css_file + '" />\n'
        body = {'headerTags': links_stylesheets}
        body = json.dumps(body, sort_keys=True)
    
        return scrapy.Request('https://smbwebmgr.internetbrands.com/api/sites/' + site_id,\
                              method='PUT', headers=headers, body=body, callback=self.callback_css)

    def post_redirect(self, legacy_url, smb_slug, access_token, site_id):
        """POST 301 redirects to smbwegmgr usings its API.
        """

        headers = {'Content-Type':'application/json', 'Authorization':'Bearer ' + access_token}
        body = {'type':'0', 'matchType':'0', 'fromUrl':legacy_url, 'toUrl':smb_slug}
        body = json.dumps(body, sort_keys=True)
    
        return scrapy.Request('https://smbwebmgr.internetbrands.com/api/sites/' + site_id + \
            '/page_redirects/', method='POST', headers=headers, body=body, \
            callback=self.callback_redirect)

    def post_page(self, title, url_slug, layout, content, seo_title, seo_keywords, seo_description, access_token, site_id):
        """POST a new page to smbwebmgr using its API.
        """

        headers = {'Content-Type':'application/json', 'Authorization':'Bearer ' + access_token}
        body = {'title':title,
                'url':url_slug,
                'layout': layout,
                'content':content,
                'meta_title':seo_title,
                'meta_keywords':seo_keywords,
                'meta_description':seo_description}
        body = json.dumps(body, sort_keys=True)
    
        return scrapy.Request('https://smbwebmgr.internetbrands.com/api/sites/' + site_id + \
            '/pages/', method='POST', headers=headers, body=body, \
            callback=self.callback_page, errback=self.errback_page)
    

    def put_logo(self, alias_name, access_token, site_id, title='', description='', logo_src=''):
        """PUT the business name, tagline, and logo image to SMBWEBMGR using its API.
        """

        headers = {'Content-Type':'application/json', 'Authorization':'Bearer ' + access_token}
        body = {'title': title,
                'description': description,
                'imagePath': logo_src,
                'alt_text':'Logo',
                'showImage':'true',
                'showTitle':'true',
                'showDescription':'true',
                'moduleVisibility':{'mobile':'true','desktop':'true','tablet':'true'}
                }
        body = json.dumps(body, sort_keys=True)
    
        return scrapy.Request('https://smbwebmgr.internetbrands.com/api/sites/' + site_id + \
            '/logos/' + alias_name, method='PUT', headers=headers, body=body, \
            callback=self.callback_logo)

    def put_locations(self, alias_name, access_token, site_id):
        """PUT to set the location for the business to SMBWEBMGR using its API.
        """
        headers = {'Content-Type':'application/json', 'Authorization':'Bearer ' + access_token}
        body = {'locations': ['location1'],
                'showAddress':'true',
                'showAddress2':'true',
                'showState':'true',
                'showZip':'true',
                'showPhone':'true',
                'moduleVisibility':{'mobile':'true', 'desktop':'true', 'tablet':'true'}}
        body = json.dumps(body, sort_keys=True)
        return scrapy.Request('https://smbwebmgr.internetbrands.com/api/sites/' + site_id + \
            '/locations/' + alias_name, method='PUT', headers=headers, body=body, \
            callback=self.callback_locations, errback=self.errback_locations)

    def post_locations_O(self, name, address, address2, city, state, zip_code, \
                        country, phone, fax, email, latitude, longitude, \
                        access_token, site_id):
        """POST a new location to SMBWEBMGR using its API.
        """
        headers = {'Content-Type':'application/json', 'Authorization':'Bearer ' + access_token}
        body = {'name':name,
                'address': address,
                'address2': address2,
                'city': city,
                'state': state,
                'zip': zip_code,
                'country': country,
                'phone': phone,
                'fax': fax,
                'email': email,
                'useCoordinates': 'true' if latitude and longitude else 'false', 
                'latitude': float(latitude) if latitude != '' else None,
                'longitude': float(longitude) if longitude != '' else None
        }
        body = json.dumps(body, sort_keys=True)
    
        return scrapy.Request('https://smbwebmgr.internetbrands.com/api/sites/' + site_id + \
            '/locations/', method='POST', headers=headers, body=body, \
            callback=self.callback_locations_O, errback=self.errback_locations_O)
            

    def post_hours_O(self, hours, access_token, site_id):
        """Add news sets of office hours to SMBWEBMGR via its API.
        """
        headers = {'Content-Type':'application/json', 'Authorization':'Bearer ' + access_token}
        body = hours
        body = json.dumps(body, sort_keys=True)
    
        return scrapy.Request('https://smbwebmgr.internetbrands.com/api/sites/' + site_id + \
            '/hours/', method='POST', headers=headers, body=body, \
            callback=self.callback_hours_O, errback=self.errback_hours_O)
            

    def post_socialmedia_O(self, url, label, icon_class, access_token, site_id):
        """Add new social media icons to SMBWEBMGR via its API.
        """
        headers = {'Content-Type':'application/json', 'Authorization':'Bearer ' + access_token}
        body = {'url': url,
                'label': label,
                'iconClass': icon_class
        }
        body = json.dumps(body, sort_keys=True)
    
        return scrapy.Request('https://smbwebmgr.internetbrands.com/api/sites/' + site_id + \
            '/socialmedia/', method='POST', headers=headers, body=body, \
            callback=self.callback_socialmedia_O, errback=self.errback_socialmedia_O)
            

    def put_maps(self, alias_name, access_token, site_id):
        """PUT to set the location for the business to SMBWEBMGR using its API.
        """
        headers = {'Content-Type':'application/json', 'Authorization':'Bearer ' + access_token}
        body = {'locations': ['location1'],
                'showTitle':'true',
                'showCaption':'true',
                'hue':'none',
                'icon':'spindle',
                'iconColor':'red',
                'height':'100',
                'width':'100',
                'autoFit':'true',
                'zoom':'14',
                'alwaysShowInfoWindow':'true',
                'showAddressOnHover':'false',
                'zoomControl':'true',
                'moduleVisibility':{'mobile':'true', 'desktop':'true', 'tablet':'true'}}
        body = json.dumps(body, sort_keys=True)
        return scrapy.Request('https://smbwebmgr.internetbrands.com/api/sites/' + site_id + \
            '/maps/' + alias_name, method='PUT', headers=headers, body=body, \
            callback=self.callback_maps)

    ##################################
    # Brand-Agnostic Parsing Methods #
    ##################################

    def parse_navigation(self, css_selector, response):
        """Creates a Menu Scrapy item given the CSS selector for level 1 li tags.
    
        TODO Make this method more stateless
        """
        menu_loader = ItemLoader(items.Menu())
        selector_level_1_li = response.css(css_selector)
        menu_loader.item['menu'] = []
        menu = menu_loader.item['menu']
        menu = self.traverse(selector_level_1_li, menu)
        return menu_loader.item

    def parse_menu_files(self, menu_all_urls):
        """Iterates through all menu links and POST file if found.
    
        TODO Make this method more stateless.
        """
        for url in menu_all_urls:
            if self.check_if_internal(url):
                if self.check_if_file(url):
                    filename = self.get_filename(url)
                    filename = self.sanitize_filename(filename)
                    if self.check_if_relative(url):
                        yield self.post_file(self.make_absolute(url), filename, self.access_token, self.site_id)
                    else:
                        yield self.post_file(url, filename, self.access_token, self.site_id)
                else:
                    pass
            else:
                pass

    def parse_stylesheets(self, stylesheet_selectors, response):
        """Upload a stylesheet and set it to be used for the smbwebmgr site.
    
        TODO Make this method more stateless.
        """

        legacy_css_filenames = []
        # If each stylesheet selector actually selects a stylesheet
        if all([response.css(selector) for selector in stylesheet_selectors]):
            for selector in stylesheet_selectors:
                legacy_css_url = response.css(selector).xpath('@href').extract()[0]
                if self.check_if_relative(legacy_css_url):
                    legacy_css_url = self.make_absolute(legacy_css_url)
                else:
                    pass
                legacy_css_filename = self.get_filename(legacy_css_url)
                legacy_css_filename = self.sanitize_filename(legacy_css_filename)

                yield self.post_file(legacy_css_url, legacy_css_filename, self.access_token, self.site_id)

                legacy_css_filenames.append(legacy_css_filename)
                

            yield self.put_css(legacy_css_filenames, self.access_token, self.site_id)
        else:
            pass

    def map_urls(self, menu, key_url, key_x):
        """Returns a dictionary of legacy url to new slug pairs.
    
        TODO Make this method more stateless.
        """
        mapping_dict = {}
        for legacy_url, smb_slug in zip(self.generate_values(menu, key_url), \
                                        self.generate_values(menu, key_x)):
            if legacy_url != '#':
                if self.check_if_internal(legacy_url):
                    if self.check_if_relative(legacy_url):
                        legacy_url = self.make_absolute(legacy_url)
                    elif self.check_if_file(legacy_url):
                        legacy_filename = self.get_filename(legacy_url)
                        legacy_filename = self.sanitize_filename(legacy_filename)
                        smb_slug = self.editor_url[0:-15] + \
                                'storage/app/media/' + \
                                legacy_filename
                    else:
                        pass

                    if 'http' not in legacy_url:
                        legacy_url = self.get_http(self.website.url) + legacy_url
                    else:
                        pass

                    mapping_dict[legacy_url] = smb_slug
                else:
                    pass
            else:
                pass
        
        return mapping_dict

    def create_redirects(self, mapping_dict):
        """Create 301 redirects for each link in the menu.
    
        TODO Make this method more stateless.
        """
        for legacy_url in mapping_dict:
            # Use path only--not the whole URL provided
            #      OLD               NEW
            # /services.html  ->  /services


            legacy_url_path = urlparse(legacy_url).path
            legacy_url_path = '/' +  legacy_url_path.split('/')[-1]
            if self.check_if_file(legacy_url):
                continue
            # Check to prevent pages redirecting to themselves
            elif legacy_url_path == mapping_dict[legacy_url]:
                continue
            # Do not set a redirect for the home page
            elif legacy_url == self.website.url:
                continue
            #checks if the url is the home page without a trailing /
            elif legacy_url == self.website.url[:-1]:
                continue
            #Do not set up redirects for articles
            elif 'articles/' in legacy_url or 'articles_dear_doctor' in legacy_url:
                continue
            # Redirect 'index.html' links to the base url home page
            elif 'index' in legacy_url:
                mapping_dict[legacy_url] = '/'
            else:
                yield self.post_redirect(legacy_url_path, mapping_dict[legacy_url], \
                                            self.access_token, self.site_id)

    def parse_page(self, response):
        """Generalized method to process pages.
    
        TODO Make this method more stateless.
        """
    
        print('Scraping ' + response.request.url + ' ...', flush=True)
        logger_friendly.info('Scraping ' + response.request.url + ' ...')
    
    
        # Process SEO, links, images, etc. in page content
        seo_title = response.xpath('//meta[@name="title"]/@content').extract_first()

        if seo_title is None:
            seo_title = response.xpath('//title/text()').extract_first()

        seo_keywords = response.xpath('//meta[@name="keywords"]/@content').extract_first()
        seo_description = response.xpath('//meta[@name="description"]/@content').extract_first()





        # Make sure SEO keywords are no more than 10 comma seperated phrases and
        # less than 300 characters
        if seo_keywords:
            seo_keywords = ','.join(seo_keywords.split(',')[0:8])[0:299]
        # Make sure SEO description is less than 500 characters
        if seo_description:
            seo_description = seo_description[0:495]
    
        # Parse only the 'main content' of each legacy web page
        if '#' in self.website.main_content_selector:
            content_id = self.website.main_content_selector.replace('#', '')
            strainer = SoupStrainer(id=content_id)
        else:
            content_class = self.website.main_content_selector.replace('.','')
            strainer = SoupStrainer(class_=content_class)
    
        soup = BeautifulSoup(response.text, 'lxml', parse_only=strainer)
    

        # Compile regex to be used multiple times later
        regex_baystone_gallery = re.compile('baystonemedia.*?image\/gallery')
        regex_baystone_source = re.compile('gallery.*?slide')
    

        #loops through every link
        for link in soup.find_all(href=self.deny_links) + soup.find_all(src=self.deny_links):
            if link.name == 'a':
                path = link['href']
            elif link.name == 'img':
                path = link['src']
            else:
                # Neither a tag nor img tag; could be a link tag, etc.
                continue
    
            # Check if this link is a page jump, if so ignore it and continue
            if path[0] == '#':
                continue
            else:
                pass

            #checks if
    
            if 'articles/' in path or 'articles_dear_doctor/' in path:
                continue
            else:
                pass

            # Check if the link ends with a trailing '/' slash; if so, remove
            if path[-1] == '/' and link.name == 'a':
                path = path[:-1]
            else:
                pass
    
            if self.check_if_internal(path):

                #checks if link is a file
                if self.check_if_file(path):

                    #if it is, processes the link as a file
                    if self.check_if_relative(path):
                        path = self.make_absolute(path)
                        path_filename = self.get_filename(path)
                        path_mm_filename = self.sanitize_filename(path_filename)
                        # Percent encode the space character if present
                        if ' ' in path:
                            path = path.replace(' ', '%20')
                        else:
                            pass
                        yield self.post_file(path, path_mm_filename, self.access_token, self.site_id)
                        if link.name == 'a':
                            link['href'] = self.editor_url[0:-15] + 'storage/app/media/' + path_mm_filename
                        else:
                            link['src'] = self.editor_url[0:-15] + 'storage/app/media/' + path_mm_filename
    
                    else:
                        path_filename = self.get_filename(path)
                        path_mm_filename = self.sanitize_filename(path_filename)
                        # Check if the image src is a legacy Baystone Media gallery image path
                        # If so, change the path so that we get the original size image
                        if regex_baystone_gallery.search(path):
                            path = regex_baystone_source.sub('source', path)
                        else:
                            pass
                        yield self.post_file(path, path_mm_filename, self.access_token, self.site_id)
                        if link.name == 'a':
                            link['href'] = self.editor_url[0:-15] + 'storage/app/media/' + path_mm_filename
                        else:
                            link['src'] = self.editor_url[0:-15] + 'storage/app/media/' + path_mm_filename
                #if not a file
                else:
                    
                    if self.check_if_relative(path):
                        path = self.make_absolute(path)
                        if path not in self.mapping_dict:

                            yield scrapy.Request(path, callback=self.parse_page)

                            # Rename path for how it will be created on smbwebmgr
                            path_path = urlparse(path).path

                            path_uri = path_path.split('/')[-1]
                            if '.' in path_uri:
                                path_uri = path_uri.split('.')[0]

                            path_slug = slugify(path_uri)
    
                            if '-' not in path_slug:
                                hyphen_slug = ''
                                path_split_num = [re.split(r'(\d+)',s) for s in [path_slug]]
                                for part in path_split_num[0]:
                                    if part != '':
                                        path_split_word = wordninja.split(part)
                                        hyphen_slug = hyphen_slug + '-'.join(path_split_word) + '-'
                                    else:
                                        continue
                                hyphen_slug = hyphen_slug.rstrip('-')
                                path_slug = hyphen_slug
                            else:
                                pass
    
                            link['href'] = path_slug
                        else:
                            link['href'] = self.mapping_dict[path].split('/')[-1]
                    else:


                        if path not in self.mapping_dict:

                            if 'https:' not in path or 'http:' not in path:
                                continue


                            yield scrapy.Request(path, callback=self.parse_page)
                            # Rename path for how it will be created on smbwebmgr
                            path_path = urlparse(path).path
                            path_uri = path_path.split('/')[-1]
                            if '.' in path_uri:
                                path_uri = path_uri.split('.')[0]
                            path_slug = slugify(path_uri)

    
                            if '-' not in path_slug:
                                hyphen_slug = ''
                                path_split_num = [re.split(r'(\d+)',s) for s in [path_slug]]
                                for part in path_split_num[0]:
                                    if part != '':
                                        path_split_word = wordninja.split(part)
                                        hyphen_slug = hyphen_slug + '-'.join(path_split_word) + '-'
                                    else:
                                        continue
                                hyphen_slug = hyphen_slug.rstrip('-')
                                path_slug = hyphen_slug
                            else:
                                pass
    
                            link['href'] = path_slug
                        else:
                            link['href'] = self.mapping_dict[path].split('/')[-1]
            else:
                continue
    
        


        # Instead of Officite legacy 'library' pages, go to the patient education.
        for link in soup.find_all(href=self.get_lib_links):
            link['href'] = 'articles'
    
        # Remove unwanted legacy markup
    
        # Remove legacy form leads
        for form in soup.find_all(class_='feature_form'):
            form.decompose()
    
        # Remove legacy form leads
        for form in soup.find_all('form'):
            form.decompose()
    
        # Remove legacy library side bars
        for library_wrapper in soup.find_all(class_='library_wrapper'):
            library_wrapper.decompose()
    
        # Remove legacy search function
        for search_form in soup.find_all(class_='librarySearchForm'):
            search_form.decompose()
    
        # Remove legacy editor maps
        for google_map in soup.find_all(class_='feature_map'):
            google_map.decompose()
    
        # Remove legacy galleries
        for gallery_old in soup.find_all(class_='feature_gallery'):
            gallery_old.decompose()
    
        # POST content for the page to smbwebmgr via its API
    
        request_url = response.request.url
        # Remove any trailing '/' in request_url
        if request_url[-1] == '/':
            request_url = request_url[:-1]
        else:
            pass
        # Create page parameters based on the link
        if request_url == self.website.url or \
            request_url + '/' == self.website.url:
            url_slug = '/'
            title = 'Welcome!'
            layout = 'home'
        elif 'index' in urlparse(request_url).path:
            url_slug = '/'
            title = 'Welcome!'
            layout = 'home'
        elif request_url in self.mapping_dict:
            url_slug = self.mapping_dict[request_url]
            title = self.mapping_dict_titles[request_url]
            layout = 'fullwidth'
        else:
            # If a link got this far, it must be a new, internal link not seen previously
            # Scrapy's built-in duplicate filter should prevent the same internal link from
            # being crawled multiple times.
            path_path = urlparse(request_url).path
            path_uri = path_path.split('/')[-1]



            if '.' in path_uri:
                path_uri = path_uri.split('.')[0]
            else:
                pass
    
            path_slug = slugify(path_uri)
            if '-' not in path_slug:
                title = ''
                hyphen_slug = ''
                path_split_num = [re.split(r'(\d+)',s) for s in [path_slug]]
                for part in path_split_num[0]:
                    if part != '':
                        path_split_word = wordninja.split(part)
                        hyphen_slug = hyphen_slug + '-'.join(path_split_word) + '-'
                        title = title + ' '.join(path_split_word) + ' '
                    else:
                        continue
                hyphen_slug = hyphen_slug.rstrip('-')
                url_slug = '/' + hyphen_slug
                title = title.rstrip(' ')
                title = title.title()
            else:
                url_slug = '/' + path_slug
                path_slug = path_slug.replace('-', ' ')
                title = path_slug.title()
    
    
    
            layout = 'fullwidth'
            # Create 301 a redirect for this unique, internal page
            page_url_dict = {request_url:url_slug}
            yield from self.create_redirects(page_url_dict)



        yield self.post_page(title, url_slug, layout, soup.prettify(), seo_title, \
                                seo_keywords, seo_description, self.access_token, \
                                self.site_id)


    def parse_logo(self, title='', description='', logo_src=''):
        """Uploads and configure the logo of a website.
    
        TODO Improve this method; redundant or misguided logic.
        """
        if self.check_if_internal(logo_src):
            if self.check_if_file(logo_src):
                logo_filename = self.get_filename(logo_src)
                logo_filename = self.sanitize_filename(logo_filename)
                if self.check_if_relative(logo_src):
                    logo_src = self.make_absolute(logo_src)
                    yield self.post_file(logo_src, logo_filename, self.access_token, self.site_id)
                else:
                    yield self.post_file(logo_src, logo_filename, self.access_token, self.site_id)
            else:
                logo_filename = ''
        else:
            logo_filename = ''
    
        if logo_src != '':
            logo_filename = '/' + logo_filename
        else:
            pass

    
        yield self.put_logo('logo_header', self.access_token, self.site_id, title=title, \
                            description=description, logo_src=logo_filename)
        yield self.put_logo('logo_home', self.access_token, self.site_id, title=title, \
                            description=description, logo_src=logo_filename)
        yield self.put_logo('logo_footer', self.access_token, self.site_id, title=title, \
                            description=description, logo_src=logo_filename)

    def parse_locations(self):
        """Configures all location components to use the Primary Location.
    
           This method calls the API multiple times with different alias names
           because alias name for components are not consistent between themes.
        """
        yield self.put_locations('locations_header', self.access_token, self.site_id)
        yield self.put_locations('locations_footer', self.access_token, self.site_id)
        yield self.put_locations('location_header', self.access_token, self.site_id)
        yield self.put_locations('location_footer', self.access_token, self.site_id)

    def parse_locations_O(self, legacy_data):
        """Configures all location components using data from the legacy API for Officite.
        """
        for location in legacy_data['data']['locations']:
            name = location['name']
            address = location['address1']
            address2 = location['address2']
            city = location['city']
            state = location['state']
            zip_code = location['zip']
            country = location['country']
            phone = location['phone1']
            fax = location['fax']
            email = location['email']
            latitude = location['map_lat']
            longitude = location['map_long']
            yield self.post_locations_O(name, address, address2, city, state, zip_code, \
                                 country, phone, fax, email, latitude, longitude, \
                                 self.access_token, self.site_id)
    

    def parse_hours_O(self, legacy_data):
        """Configures hours components using data from the legacy API for Officite.
        """
        for location in legacy_data['data']['locations']:
            if location['hours']:
                num_day_map = {'1':'sunday','2':'monday', '3':'tuesday', '4':'wednesday', '5':'thursday', '6':'friday', '7':'saturday'}
                # Ensure the hours data set name is less than 50 characters
                hours = {'name': location['name'][:40] + ' Hours'}
                days = {}
                for day in location['hours'].split(','):
                    day_split = day.split(':')
                    day_open = 'true'
                    day_name = num_day_map[day_split[0]]
                    day_title = day_name.title()
                    time1_open = day_split[1].lstrip('0') + ':' + day_split[2] + ' ' + day_split[3]
                    time1_close = day_split[4].lstrip('0') + ':' + day_split[5] + ' ' + day_split[6]
                    day_data ={
                        'open': day_open,
                        'day_name': day_title,
                        'time1_open': time1_open,
                        'time1_close': time1_close,
                        'time2_open': '',
                        'time2_close': '',
                        'time3_open': '',
                        'time3_close': ''
                    }
                    # Add day to the days dict
                    days[day_name] = day_data
                hours['days'] = days
                yield self.post_hours_O(hours, self.access_token, self.site_id)
            else:
                continue
    

    def parse_socialmedia_O(self, legacy_data):
        """Configures socialmedia components using data from the legacy API for Officite.
        """
        for socialmedia in legacy_data['data']['socialMedia']:
            if socialmedia['token'] == 'facebook_domain':
                url = 'https://www.facebook.com/' + socialmedia['value']
                label = 'Facebook'
                icon_class = 'icon-facebook'
                yield self.post_socialmedia_O(url, label, icon_class, self.access_token, self.site_id)
            elif socialmedia['token'] == 'twitter_username':
                url = 'https://www.twitter.com/' + socialmedia['value']
                label = 'Twitter'
                icon_class = 'icon-twitter'
                yield self.post_socialmedia_O(url, label, icon_class, self.access_token, self.site_id)
            elif socialmedia['token'] == 'Yelp_url':
                url = socialmedia['value']
                label = 'Yelp'
                icon_class = 'icon-yelp'
                yield self.post_socialmedia_O(url, label, icon_class, self.access_token, self.site_id)
            elif socialmedia['token'] == 'GooglePlus_url':
                url = socialmedia['value']
                label = 'Google Plus'
                icon_class = 'icon-google-plus'
                yield self.post_socialmedia_O(url, label, icon_class, self.access_token, self.site_id)
            elif socialmedia['token'] == 'YouTube_url':
                url = socialmedia['value']
                label = 'YouTube'
                icon_class = 'icon-youtube'
                yield self.post_socialmedia_O(url, label, icon_class, self.access_token, self.site_id)
            else:
                continue
    
    

    def parse_maps(self):
        """Configures all map components to use the Primary Location.
    
           This method calls the API multiple times with different alias names
           because alias name for components are not consistent between themes.
        """
        yield self.put_maps('map_home', self.access_token, self.site_id)
        yield self.put_maps('map_body', self.access_token, self.site_id)
        yield self.put_maps('map_fullwidth', self.access_token, self.site_id)
        yield self.put_maps('map_contact', self.access_token, self.site_id)

    def get_http(self, url):
        if 'https:' in url:
            return 'https:'
        else:
            return 'http:'