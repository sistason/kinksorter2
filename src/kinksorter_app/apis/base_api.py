import requests
import logging
import json
import threading
import time


class BaseAPI:
    name = 'BaseAPI'

    def __init__(self):
        logging.getLogger("requests").setLevel(logging.WARNING)
        self._site_capabilities = None
        self.database = {}

    def get_site_responsibilities(self):
        """ Get responsibilities, e.g. which directory-name (==subsite) this API is capable of """
        if self._site_capabilities is not None:
            return self._site_capabilities

        resps = self._get_site_responsibilities()

        return resps if resps is not None else []

    @NotImplementedError
    def _get_site_responsibilities(self):
        """ Get the site directly from the site """
        return

    @staticmethod
    def _to_json(result):
        """ Helper to convert a string to JSON """
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {}

    @NotImplementedError
    def query(self, type_, by_property_, value_):
        """ Use the API to get an item of "type" with by_property matching with query"""
        return
