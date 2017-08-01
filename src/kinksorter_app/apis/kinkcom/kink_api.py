import logging
import datetime
import re

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from kinksorter_app.apis.kinkcom.kink_recognition import KinkRecognition
from kinksorter_app.apis.base_api import BaseAPI

from kinksorter_app.apis.kinkcom.models import KinkComSite, KinkComPerformer, KinkComShoot


class KinkAPI(BaseAPI):
    name = 'Kink.com'

    def __init__(self):
        super().__init__()
        self.recognition = KinkRecognition(self)

    def _get_site_responsibilities(self):
        channel_names = []
        for site in KinkComSite.objects.all():
            channel_names.append(site.name)
            channel_names.append(''.join([n[0] for n in site.name.split()]))

        return channel_names if channel_names else None

    def get_correct_model(self):
        return KinkComShoot

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
                    date_obj = datetime.date.fromtimestamp(int(date))
                else:
                    date_obj = datetime.datetime.strptime(date, '%Y-%m-%d').date()
                shoots_ = self._get_shoots_by_date(date_obj)
            except ValueError:
                logging.error('Cannot recognize date format, must be %Y-%m-%d or %s, was "{}"'.format(date))
                shoots_ = KinkComShoot.objects.none()
        elif performer_numbers:
            shoots_ = self._get_shoots_by_performer_numbers(performer_numbers)
        elif performer_name:
            shoots_ = self._get_shoots_by_performer_names(performer_name)
        else:
            shoots_ = KinkComShoot.objects.none()

        return shoots_

    def performer(self, performer_name=None, performer_number=None):
        if performer_number:
            performers_ = self._get_performers_by_number(performer_number)
        elif performer_name:
            performers_ = self._get_performers_by_name(performer_name)
        else:
            performers_ = KinkComPerformer.objects.none()

        return performers_

    def site(self, name=None, name_main=None):
        return self._get_sites_by_name(name, name_main)

    @staticmethod
    def _get_sites_by_name(name, name_main):
        if name_main is not None:
            return KinkComSite.objects.filter(is_partner=False).filter(name__iregex=name_main)
        if name is not None:
            return KinkComSite.objects.filter(name__iregex=name)
        return KinkComSite.objects.none()

    @staticmethod
    def _get_performers_by_number(performer_number):
        try:
            return KinkComPerformer.objects.filter(number=performer_number)
        except (ObjectDoesNotExist, ValueError):
            return KinkComPerformer.objects.none()
        except MultipleObjectsReturned:
            performers = KinkComShoot.objects.filter(number=performer_number)
            [p.delete() for p in performers[1:]]
            return performers

    def _get_performers_by_name(self, performer_name):
        if ',' in performer_name:
            performer_name = re.sub(r',', self._replace_repetitions_with_or, performer_name)
            performer_name = '|'.join(p.strip() for p in performer_name.split('|'))
        return KinkComPerformer.objects.filter(name__iregex=performer_name)

    def _get_shoots_by_performer_names(self, performer_name):
        performers_ = self._get_performers_by_name(performer_name)
        performer_numbers_ = ','.join(str(v[0]) for v in performers_.values_list('number'))
        return self._get_shoots_by_performer_numbers(performer_numbers_)

    @staticmethod
    def _replace_repetitions_with_or(match):
        """ Replaces a comma only if it is not a comma in an repetition statement """
        if re.match(r'\{\d,\d?\}', match.string[match.start() - 2:match.end() + 2]):
            return 'r'
        return '|'

    @staticmethod
    def _get_shoots_by_shootid(shootid):
        if not shootid:
            return KinkComShoot.objects.filter(exists=True).latest('shootid')
        else:
            shoots = KinkComShoot.objects.filter(shootid=shootid)
            if shoots.count() > 1:
                [s.delete() for s in shoots[1:]]
            return shoots

    @staticmethod
    def _get_shoots_by_title(title):
        return KinkComShoot.objects.filter(title__iregex=title)

    @staticmethod
    def _get_shoots_by_date(date_obj):
        return KinkComShoot.objects.filter(date=date_obj)

    @staticmethod
    def _get_shoots_by_performer_numbers(performer_numbers):
        all_ = KinkComShoot.objects.all()
        for number in re.split(r'\D', performer_numbers):
            all_ = all_.filter(performers__number=number)
        return all_
