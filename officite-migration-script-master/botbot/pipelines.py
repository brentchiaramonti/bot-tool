# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import items
from scrapy.pipelines.media import MediaPipeline
from scrapy.exceptions import DropItem

import pdb

class BotBotPipeline(MediaPipeline):
    """Processes items and sends data to smbwebmgr via its API.

    Rather than persisting data locally, all data is sent directly to
    smbwebmgr via its API. This includes images in web page content,
    documents in web page content, etc. The pipline avoids making the
    same request multiple times. If an image is used multiple times
    throughout a website, it will only be uploaded once. This class takes
    advantage of the overridable interface of its parent.

    TODO Add image and file download capability.
    """
    def get_media_requests(self, item, info):
        raise DropItem
