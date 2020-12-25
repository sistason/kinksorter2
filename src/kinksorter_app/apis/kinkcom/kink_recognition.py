import os
import logging

from kinksorter_app.apis.kinkcom.kink_recognition_methods import KinkRecognitionMethods


class KinkRecognition:
    def __init__(self, api):
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.methods = KinkRecognitionMethods(template_dir)
        self.api = api

    def recognize(self, movie, override_name='', override_sid=0, extensive=False):
        logging.debug('"{}" - recognizing...'.format(movie.file_name))

        results = None
        if override_sid and type(override_sid) == int:
            shootid, sure = override_sid, True
        else:
            if override_name:
                shootid, sure = self.get_shootid(override_name, name_override=True)
            else:
                shootid, sure = self.get_shootid(movie.full_path, extensive=extensive)
        if shootid:
            results = self.api.query('shoot', 'shootid', shootid)

        if results is not None and len(results) > 0:
            return results[0].get('shootid')
        else:
            logging.info('"{}" - Nothing found, leaving untagged'.format(movie.file_name))

    def get_shootid(self, file_path, name_override=False, extensive=False):
        shootid, shootid_cv, shootid_md, shootids_nr, sure = 0, -1, 0, [], False

        file_name = os.path.basename(file_path) if not name_override else file_path

        shootids_nr = self.methods.get_shootids_from_filename(file_name)
        try:
            shootid_md = self.methods.get_shootid_through_metadata(file_path)
        except AttributeError:
            shootid_md = 0

        if shootids_nr and shootid_md:
            # When metadata and filename match, we are sure
            sure = shootid_md in shootids_nr
            shootid = shootid_md
        else:
            try:
                shootid_cv = self.methods.get_shootid_through_image_recognition(file_path, extensive=extensive)
                # when cv is supported by one more method, we are sure
                sure = shootid_cv and (shootid_cv in shootids_nr or shootid_cv == shootid_md)
                shootid = shootid_cv
            except AttributeError:
                shootid_cv = 0

        logging.debug(f'Found shootids {"sure" if sure else "unsure"} '
                      f'- cv: {shootid_cv}; md: {shootid_md}; nr: {shootids_nr}')

        if sure:
            if shootid < 1000:
                logging.info('File "{}" has shootid<1000. Check this, could be wrongly detected'.format(file_path))
            logging.debug(f"Solution for {file_name}: {shootid} (Sure)")
            return shootid, sure

        # Handling of unsure cases

        if shootid_cv:
            logging.debug(f"Solution for {file_name}: {shootid_cv} (Unsure, trust cv)")
            return shootid_cv, sure

        if shootid_md:
            logging.debug(f"Solution for {file_name}: {shootid_md} (Unsure, trust md)")
            return shootid_md, sure

        if shootids_nr:
            logging.debug(f"Solution for {file_name}: {shootids_nr} (Unsure, trust last nr)")
            return shootids_nr[-1], sure

        return 0, False
