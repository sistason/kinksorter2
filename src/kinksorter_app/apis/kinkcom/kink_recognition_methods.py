import mutagen
import logging
import os
import re
import sys
import json

from kinksorter_app.apis.kinkcom.kink_recognition_cv import KinkRecognitionCv


class KinkRecognitionMethods:
    UNLIKELY_NUMBERS = {'quality': [360, 480, 720, 1080, 1440, 2160],
                        'date': list(range(1970, 2030))}

    def __init__(self, template_directory):
        self.cv_recognition = KinkRecognitionCv(template_directory)

        # Filter out dates like 091224 or (20)150101
        self._unlikely_shootid_date_re = re.compile(r'([01]\d)({})({})'.format(
            '|'.join(['{:02}'.format(i) for i in range(1, 13)]),
            '|'.join(['{:02}'.format(i) for i in range(1, 32)])
        ))

    def get_shootid_through_image_recognition(self, file_path, extensive=False):
        if extensive:
            return self.cv_recognition.get_shootid_through_image_recognition_extensive(file_path)
        return self.cv_recognition.get_shootid_through_image_recognition(file_path)

    def get_shootids_from_filename(self, file_name):
        search_shootid = []

        # \D does not match ^|$, so we pad it with something irrelevant
        search_name = '%' + file_name + '%'

        search_match = 1
        while search_match:
            search_name = search_name[search_match.end() - 1:] if search_match != 1 else search_name

            # Search with re.search instead of re.findall, as pre/post can be interleaved and regexps capture
            search_match = re.search(r"(\D)(\d{2,6})(\D)", search_name)
            if search_match:
                pre_, k, post_ = search_match.groups()
                shootid = int(k)
                if shootid in self.UNLIKELY_NUMBERS['date']:
                    continue
                if self._unlikely_shootid_date_re.search(k):
                    logging.debug('Most likely no shootid ({}), but a date. Skipping...'.format(k))
                    continue
                if shootid < 200:
                    continue
                if shootid in self.UNLIKELY_NUMBERS['quality'] and (pre_ != '(' or post_ != ')'):
                    logging.debug('Most likely no shootid ({}{}{}), but a quality. Skipping...'.format(pre_, k, post_))
                    continue
                if pre_ in ['(', '['] and post_ in [')', ']']:
                    return [shootid]

                search_shootid.append(shootid)

        if len(search_shootid) > 1:
            logging.info('Multiple Shoot IDs found')

        return search_shootid

    @staticmethod
    def get_shootid_through_metadata(file_path):
        """ Works only on Kink.com movies from around 3500-4500 (or with our own tags) """
        try:
            metadata = mutagen.File(file_path)
        except mutagen.MutagenError:
            metadata = None

        if metadata is not None:
            try:
                # the original, legacy Title of shootids 3500-4500
                title = metadata.get('Title')
                if title:
                    return re.search(r"Production: (<?P=shoot_id>\d+)\.", title).group("shoot_id")
                else:
                    # Kinksorter writes metadata with kinksorter_*
                    return int(metadata.get("kinksorter_shootid"))
            except (ValueError, TypeError, AttributeError):
                return 0

        return 0


if __name__ == '__main__':
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    krm = KinkRecognitionMethods(template_dir)

    file_path = os.path.abspath(sys.argv[1])
    print('cv: ', krm.get_shootid_through_image_recognition(file_path))
    print('md: ', krm.get_shootid_through_metadata(file_path))
    print('nr: ', krm.get_shootids_from_filename(file_path))
