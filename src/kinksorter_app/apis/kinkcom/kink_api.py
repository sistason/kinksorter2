import logging
import datetime
import re
import os
import json

from kinksorter_app.apis.kinkcom.kink_recognition import KinkRecognition
from kinksorter_app.apis.base_api import BaseAPI


class KinkAPI(BaseAPI):
    name = 'Kink.com'

    def __init__(self):
        super().__init__()
        self._load_database()
        self.recognition = KinkRecognition(self)

    def _load_database(self):
        with open(os.path.join(os.path.dirname(__file__), 'kinkyapi.json')) as f:
            self.database = json.load(f)

    def _get_site_responsibilities(self):
        channel_names = []
        for site in self.database.get('sites', []):
            name = site.get('name', '')
            channel_names.append(name)
            channel_names.append(''.join([n[0] for n in name.split()]))

        return channel_names if channel_names else None

    def recognize(self, *args, **kwargs):
        return self.recognition.recognize(*args, **kwargs)

    def query(self, type_, by_property, value):
        res = None
        if type_ == 'shoot':
            res = self.shoot(**{by_property: value})
        if type_ == 'performer':
            res = self.performer(**{by_property: value})
        if type_ == 'sites':
            res = self.site(**{by_property: value})

        return res

    def shoot(self, shootid=None, title=None, date=None, performer_numbers=None, performer_name=None):
        if shootid is not None:
            shoots_ = self._get_shoots_by_shootid(shootid)
        elif title:
            shoots_ = self._get_shoots_by_title(title)
        elif date:
            try:
                if date.isdigit():
                    date_ts = int(date)
                else:
                    date_ts = int(datetime.datetime.strptime(date, '%Y-%m-%d').date().strftime('%s'))
                shoots_ = self._get_shoots_by_date(date_ts)
            except ValueError:
                logging.error('Cannot recognize date format, must be %Y-%m-%d or %s, was "{}"'.format(date))
                shoots_ = []
        elif performer_numbers:
            shoots_ = self._get_shoots_by_performer_numbers(performer_numbers)
        elif performer_name:
            shoots_ = self._get_shoots_by_performer_names(performer_name)
        else:
            shoots_ = []

        return shoots_

    def performer(self, performer_name=None, performer_number=None):
        if performer_number:
            performers_ = self._get_performers_by_number(performer_number)
        elif performer_name:
            performers_ = self._get_performers_by_name(performer_name)
        else:
            performers_ = []

        return performers_

    def site(self, name=None, name_main=None):
        return self._get_sites_by_name(name, name_main)

    def _get_sites_by_name(self, name, name_main):
        if name_main is not None:
            return [site for site in self.database.get('sites', [])
                    if not site.get('partner', True) and re.search(name_main.lower(), site.get('name', '').lower())]
        if name is not None:
            return [site for site in self.database.get('sites', [])
                    if re.search(name.lower(), site.get('name', '').lower())]
        return []

    def _get_performers_by_number(self, performer_number):
        try:
            return [performer for performer in self.database.get('performers', [])
                    if performer.get('number') == performer_number]

        except ValueError:
            return []

    def _get_performers_by_name(self, performer_name):
        if ',' in performer_name:
            performer_name = re.sub(r',', self._replace_repetitions_with_or, performer_name)
            performer_name = '|'.join(p.strip() for p in performer_name.split('|'))
        return [performer for performer in self.database.get('performers', [])
            if re.search(performer_name, performer.get('name'))]

    def _get_shoots_by_performer_names(self, performer_name):
        performers_ = self._get_performers_by_name(performer_name)
        performer_numbers_ = ','.join(str(v.get('number')) for v in performers_)

        return self._get_shoots_by_performer_numbers(performer_numbers_)

    @staticmethod
    def _replace_repetitions_with_or(match):
        """ Replaces a comma only if it is not a comma in an repetition statement """
        if re.match(r'\{\d,\d?\}', match.string[match.start() - 2:match.end() + 2]):
            return 'r'
        return '|'

    def _get_shoots_by_shootid(self, shootid):
        if not shootid:
            return max([shoot for shoot in self.database.get('shoots', [])
                if shoot.get('exists')], key=lambda f: int(f.get('shootid')))
        else:
            return [shoot for shoot in self.database.get('shoots', [])
                if shoot.get('shootid') == shootid]

    def _get_shoots_by_title(self, title):
        return [shoot for shoot in self.database.get('shoots', [])
                if re.search(title, shoot.get('title'))]

    def _get_shoots_by_date(self, date_ts):
        return [shoot for shoot in self.database.get('shoots', [])
                if shoot.get('date') == date_ts]

    def _get_shoots_by_performer_numbers(self, performer_numbers):
        all_ = self.database.get('shoots', [])
        for number in re.split(r'\D', performer_numbers):
            all_ = [site for site in all_ if [p for p in site.get('performers', []) if p.get('number') == number]]
        return all_
