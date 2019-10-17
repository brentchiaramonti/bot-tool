# -*- coding: utf-8 -*-
from scrapy.loader import ItemLoader


class BotBotItemLoader(ItemLoader):
    # Override to allow for falsy values to be set for fields
    def _add_value(self, field_name, value):
        value = arg_to_iter(value)
        processed_value = self._process_input_value(field_name, value)
        #if processed_value:
        self._values[field_name] += arg_to_iter(processed_value)
