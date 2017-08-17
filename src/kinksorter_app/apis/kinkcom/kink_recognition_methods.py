import logging
import cv2
import subprocess
import os
import re
import json
import tempfile


class KinkRecognitionMethods:
    shootid_templates = []
    UNLIKELY_NUMBERS = {'quality': [360, 480, 720, 1080, 1440, 2160],
                        'date': list(range(1970, 2030))}

    def __init__(self, template_dir):
        self.shootid_templates = self._load_templates(template_dir)

        # Filter out dates like 091224 or (20)150101
        self._unlikely_shootid_date_re = re.compile('([01]\d)({})({})'.format(
            '|'.join(['{:02}'.format(i) for i in range(1, 13)]),
            '|'.join(['{:02}'.format(i) for i in range(1, 32)])
        ))

    def _load_templates(self, template_dir):
        if template_dir and os.path.exists(template_dir):
            kink_templates_ = []
            for template_ in os.scandir(template_dir):
                if template_.name.endswith('.jpeg'):
                    kink_templates_.append(template_.path)

            return [cv2.imread(t, 0) for t in sorted(kink_templates_)]
        return []

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
        """ Works only on Kink.com movies from around 3500-4500 """
        o = subprocess.run(['ffprobe', '-show_format', '-v', 'quiet', '-of', 'json', file_path], stdout=subprocess.PIPE)
        try:
            json_output = json.loads(o.stdout.decode())
            title = json_output.get('format').get('tags').get('title')
            return int(title.split('.')[0].split()[-1])
        except (ValueError, IndexError, AttributeError, json.JSONDecodeError):
            return 0

    def get_shootid_through_image_recognition(self, file_path):
        """ Works only on Kink.com movies after ~2007 """
        red_frame = self._get_fitting_frame(file_path)
        if red_frame is None:
            return -1

        shootid_crop = None
        for template in self.shootid_templates:
            template_shape, max_loc = self._match_template(red_frame, template)
            if max_loc is not None:
                shootid_crop = red_frame[max_loc[1]:max_loc[1] + template_shape[0], max_loc[0] + template_shape[1]:]

        if shootid_crop is None:
            logging.debug('Templates for shootid did not match file "{}"'.format(file_path))
            return 0

        shootid = self.recognize_shootid(shootid_crop)
        if not shootid:
            logging.debug('Tesseract couldn\'t recognize digits for file "{}"'.format(file_path))
            if logging.getLogger(self.__class__.__name__).level == logging.DEBUG:
                self.debug_frame(shootid_crop)

        return shootid

    def _match_template(self, red_frame, template):
        height, width = red_frame.shape
        # Template is for 720p image, so scale it accordingly
        scale = height / 720.0
        template_scaled = cv2.resize(template.copy(), (0, 0), fx=scale, fy=scale)
        result = cv2.matchTemplate(red_frame, template_scaled, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        return template_scaled.shape, max_loc if max_val > 0.6 else None

    def _get_fitting_frame(self, file_path):
        if not self.shootid_templates:
            logging.debug('No template to recognize shootids')
            return None

        capture = cv2.VideoCapture(file_path)
        fps, frame_count = self._prepare_capture(capture)
        if not frame_count:
            logging.debug('No frames to recognize found for file "{}"'.format(file_path))
            return None

        analysis_range = int(frame_count - 3 * fps)
        frame_steps = int(fps / 3)
        next_frame = frame_count - 1
        red_frame = None
        while red_frame is None and next_frame >= analysis_range:
            red_frame = self._get_next_frame(capture, next_frame)
            next_frame -= frame_steps

        capture.release()
        if red_frame is None:
            logging.debug('No suitable frames found in the last seconds of file "{}"'.format(file_path))
        return red_frame

    def _prepare_capture(self, capture):
        # TODO: ignore errors of capture.set of partial files
        frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = capture.get(cv2.CAP_PROP_FPS)
        # Seek until the end, or adapt the end of the file if not possible
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        frame_count = capture.get(cv2.CAP_PROP_POS_FRAMES)
        return fps, frame_count

    def _get_next_frame(self, capture, next_frame):
        capture.set(cv2.CAP_PROP_POS_FRAMES, next_frame)
        ret, frame_ = capture.read()
        if ret and frame_.any() and (frame_[:, :] > 0).sum() / frame_.size < 0.1:
            # red_frame = cv2.inRange(cv2.cvtColor(frame_, cv2.COLOR_BGR2HSV), (0, 50, 50), (30, 255, 255))
            return frame_[:, :, 2]

    @staticmethod
    def recognize_shootid(shootid_img):
        with tempfile.NamedTemporaryFile(suffix='.png') as f_:
            tmp_path = f_.name
        _, t_ = cv2.threshold(shootid_img, 100, 255, cv2.THRESH_BINARY)
        cv2.imwrite(tmp_path, t_)
        out = subprocess.run(['tesseract', tmp_path, 'stdout', 'digits'], stdout=subprocess.PIPE)
        output = out.stdout.decode()
        if ' ' in output:
            output = output.replace(' ', '')
        if output is not None and output.strip().isdigit():
            return int(output)
        return 0

    @staticmethod
    def debug_frame(frame):
        cv2.imwrite('/tmp/test.jpeg', frame)
        os.system('eog /tmp/test.jpeg 2>/dev/null')