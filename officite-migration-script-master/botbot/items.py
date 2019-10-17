# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class Business(Item):
    business_name = Field()
    logo = Field()
    locations = Field()

class Location(Item):
    location_name = Field()
    address1 = Field()
    address2 = Field()
    city = Field()
    state = Field()
    zip = Field()
    phone = Field()
    fax = Field()
    email = Field()
    lat = Field()
    long = Field()
    hours = Field()

class WebPage(Item):
    url = Field()
    url_slug = Field ()
    meta_title = Field()
    meta_keywords = Field()
    meta_description = Field()
    content = Field()
    assets = Field()
    css = Field()
    js = Field()
    menu_item = Field()

class Menu(Item):
    menu = Field()

class MenuItem(Item):
    url = Field()
    url_slug = Field()
    title = Field()
    is_parent = Field()
    parent = Field()
    children = Field()
    web_page = Field()
