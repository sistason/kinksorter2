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
        shootid_cv, shootid_md, shootid_nr = 0, 0, 0
        if not name_override:
            file_name = os.path.basename(file_path)
            try:
                shootid_cv = self.methods.get_shootid_through_image_recognition(file_path, extensive=extensive)
            except AttributeError:
                shootid_cv = 0
            try:
                shootid_md = self.methods.get_shootid_through_metadata(file_path)
            except AttributeError:
                shootid_md = 0
        else:
            file_name = file_path

        shootids_nr = self.methods.get_shootids_from_filename(file_name)
        if len(shootids_nr) > 1:
            if shootid_cv and shootid_cv in shootids_nr:
                shootid_nr = shootid_cv
            elif shootid_md and shootid_md in shootids_nr:
                shootid_nr = shootid_md
            else:
                shootid_nr = 0
        elif shootids_nr:
            shootid_nr = shootids_nr[0]

        logging.debug('Found shootids - cv: {}; md: {}; nr: {}'.format(shootid_cv, shootid_md, shootid_nr))
        sure = False
        shootid = 0
        if (shootid_nr > 0 and shootid_nr == shootid_cv) or shootid_cv > 0 or shootid_md > 0:
            # Clear solution
            sure = True
            shootid = shootid_cv if shootid_cv else shootid_md
        elif shootid_nr:
            # No image recognition, but a number is found => pre shootid-tagging in the video
            # Image recognition yields "-1" (error in video file), so trust shootid
            if shootid_nr < 1000:
                logging.info('File "{}" has shootid<1000. Check this, could be wrongly detected'.format(
                    file_path))
            elif shootid_nr > 8000 and shootid_cv != -1:
                logging.info('File "{}" has the wrong API or is (mildly) corrupted'.format(
                    file_path))
            else:
                sure = True

            shootid = shootid_nr
        logging.debug('Chose shootid {}, sure: {}'.format(shootid, sure))
        return shootid, sure
