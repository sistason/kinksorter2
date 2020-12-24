import logging
import cv2
import os
import sys
import pytesseract
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class KinkRecognitionCv:
    shootid_templates = []

    def __init__(self, template_directory):
        self.shootid_templates = self._load_templates(os.path.join(template_directory, "shootid"))
        self.shootit_digits_templates = self._load_templates(os.path.join(template_directory, "digits"))
        if len(self.shootit_digits_templates) != 10:
            logger.error(f"Found {len(self.shootit_digits_templates)} instead of 10 digit templates at "
                         f"{os.path.join(template_directory, 'digits')}, cannot do image recognition!")
            self.shootit_digits_templates = []

    @staticmethod
    def _load_templates(template_directory):
        if not template_directory or not os.path.exists(template_directory):
            return []

        kink_templates_ = []
        for template_ in os.scandir(template_directory):
            if template_.name.endswith('.jpeg') or template_.name.endswith('.png'):
                kink_templates_.append(template_.path)

        return [cv2.imread(t, 0) for t in sorted(kink_templates_)]

    def get_shootid_through_image_recognition(self, file_path):
        """ Works only on Kink.com movies after ~2007 """
        if not self.shootid_templates or not self.shootit_digits_templates:
            logger.warning("No templates found, cannot do image recognition")
            return -1

        red_frame = self._get_fitting_frame(file_path)
        if red_frame is None:
            return -1

        shootid = 0
        for template in self.shootid_templates:
            template_shape, max_loc, max_val = self._match_template(red_frame, template)
            if max_val > 0.6:
                shootid_crop = red_frame[max_loc[1]:max_loc[1] + template_shape[0], max_loc[0] + template_shape[1]:]
                if not shootid_crop.any():
                    continue

                # shootid = self._recognize_shootid_tesseract(shootid_crop)
                shootid = self._recognize_shootid_templates(shootid_crop)

        if not shootid:
            logger.debug('Couldn\'t recognize digits with OpenCV for file "{}"'.format(file_path))

        return shootid

    def get_shootid_through_image_recognition_extensive(self, file_path):
        """ Search every 3secs for the image, for all those slightly off videos. Takes around 2mins per video! """
        if not self.shootid_templates or not self.shootit_digits_templates:
            logger.warning("No templates found, cannot do image recognition")
            return -1

        capture = cv2.VideoCapture(file_path)
        fps, frame_count = self._prepare_capture(capture)
        if not frame_count:
            logger.debug('No frames to recognize found for file "{}"'.format(file_path))
            return None

        frame_steps = int(3 * fps)
        next_frame = frame_count - 1

        shootid = 0
        # VideoCapture throws hundreds of stderr-ffmpeg decode errors if the file is corrupt
        with stderr_redirected():
            while not shootid and next_frame > 0:
                capture.set(cv2.CAP_PROP_POS_FRAMES, next_frame)

                ret, frame_ = capture.read()
                if False and ret and frame_.any() and (frame_[:, :] > 0).sum() / frame_.size < 0.1:
                    # red_frame = cv2.inRange(cv2.cvtColor(frame_, cv2.COLOR_BGR2HSV), (0, 50, 50), (30, 255, 255))
                    red_frame = frame_[:, :, 2]

                    for template in self.shootid_templates:
                        template_shape, max_loc, max_val = self._match_template(red_frame, template)
                        if max_val > 0.6:
                            shootid_crop = red_frame[max_loc[1]:max_loc[1] + template_shape[0],
                                           max_loc[0] + template_shape[1]:]
                            if not shootid_crop.any():
                                continue

                            shootid = self._recognize_shootid_templates(shootid_crop)
                            if shootid:
                                return shootid

                next_frame -= frame_steps

            capture.release()

    @staticmethod
    def _match_template(red_frame, template):
        height, width = red_frame.shape
        # Template is for 720p image, so scale it accordingly
        scale = height / 720.0
        template_scaled = cv2.resize(template.copy(), (0, 0), fx=scale, fy=scale)
        result = cv2.matchTemplate(red_frame, template_scaled, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        return template_scaled.shape, max_loc, max_val

    def _get_fitting_frame(self, file_path):
        capture = cv2.VideoCapture(file_path)
        fps, frame_count = self._prepare_capture(capture)
        if not frame_count:
            logger.debug('No frames to recognize found for file "{}"'.format(file_path))
            return None

        analysis_range = int(frame_count - 3 * fps)
        frame_steps = int(fps / 3)
        next_frame = frame_count - 1
        red_frame = None

        # VideoCapture throws hundreds of stderr-ffmpeg decode errors if the file is corrupt
        with stderr_redirected():
            while red_frame is None and next_frame >= analysis_range:
                capture.set(cv2.CAP_PROP_POS_FRAMES, next_frame)
                ret, frame_ = capture.read()

                if ret and frame_.any() and (frame_[:, :] > 0).sum() / frame_.size < 0.1:
                    # red_frame = cv2.inRange(cv2.cvtColor(frame_, cv2.COLOR_BGR2HSV), (0, 50, 50), (30, 255, 255))
                    red_frame = frame_[:, :, 2]

                next_frame -= frame_steps
            capture.release()

        if red_frame is None:
            logger.debug('No suitable frames found in the last seconds of file "{}"'.format(file_path))
        return red_frame

    @staticmethod
    def _prepare_capture(capture):
        # VideoCapture throws hundreds of stderr-ffmpeg decode errors if the file is corrupt
        with stderr_redirected():
            frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT)
            fps = capture.get(cv2.CAP_PROP_FPS)
            # Seek until the end, or adapt the end of the file if not possible
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            frame_count = capture.get(cv2.CAP_PROP_POS_FRAMES)

        return fps, frame_count

    @staticmethod
    def _recognize_shootid_tesseract(shootid_img):
        _, t_ = cv2.threshold(shootid_img, 100, 255, cv2.THRESH_BINARY)
        x, y, w, h = cv2.boundingRect(t_)
        t_ = t_[y:y + h, x:x + w]
        output = pytesseract.image_to_string(t_, config=r'--psm 6 -c tessedit_char_whitelist=0123456789')
        if output:
            result = output.split("\n")[0]
            if result.isdigit():
                return int(result)

        return 0

    def _recognize_shootid_templates(self, shootid_img):
        _, img_thresholded = cv2.threshold(shootid_img, 100, 255, cv2.THRESH_BINARY)
        x, y, w, h = cv2.boundingRect(img_thresholded)
        img_thresholded_cropped = img_thresholded[y:y + h, x:x + w]

        # scale digit_templates to height of shootid_digits
        scale_factor = img_thresholded_cropped.shape[0] / self.shootit_digits_templates[0].shape[0]
        scaled_templates = [cv2.resize(template.copy(), (0, 0), fx=scale_factor, fy=scale_factor)
                            for template in self.shootit_digits_templates]

        digits_ = []
        img_digits = self._split_into_digits(img_thresholded_cropped)
        for i, img_digit in enumerate(img_digits):
            digit = self._match_digit_template(img_digit, scaled_templates)
            if not digit:
                logger.debug(f'Could not recognize the {i}th digit!')
                return 0
            digits_.append(digit)

        return int(''.join(digits_))

    @staticmethod
    def debug_frame(frame):
        _, img_thresholded = cv2.threshold(frame, 100, 255, cv2.THRESH_BINARY)
        x, y, w, h = cv2.boundingRect(img_thresholded)
        img_thresholded_cropped = img_thresholded[y:y + h, x:x + w]

        cv2.imwrite('/tmp/test.png', img_thresholded_cropped)
        os.system('eom /tmp/test.png 2>/dev/null')

    @staticmethod
    def _split_into_digits(img_thresholded_cropped):
        digits_ = []
        last_cut = 0
        for current_width in range(0, img_thresholded_cropped.shape[1]):
            if not img_thresholded_cropped[:, current_width].any():
                sequence = img_thresholded_cropped[:, last_cut:current_width]
                if sequence.any():
                    digits_.append(sequence)
                last_cut = current_width

        sequence = img_thresholded_cropped[:, last_cut:]
        if sequence.any():
            digits_.append(sequence)
        return digits_

    @staticmethod
    def _match_digit_template(img_digit, templates):
        match_results = []
        for i, template in enumerate(templates):
            result = cv2.matchTemplate(img_digit, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            match_results.append((i, max_val))

        return str(max(match_results, key=lambda t: t[1])[0])


# Thanks to https://stackoverflow.com/questions/4675728/
def fileno(file_or_fd):
    fd = getattr(file_or_fd, 'fileno', lambda: file_or_fd)()
    if not isinstance(fd, int):
        raise ValueError("Expected a file (`.fileno()`) or a file descriptor")
    return fd


@contextmanager
def stderr_redirected(to=os.devnull):
    stderr = sys.stderr
    stderr_fd = fileno(stderr)
    # copy stdout_fd before it is overwritten
    # NOTE: `copied` is inheritable on Windows when duplicating a standard stream
    with os.fdopen(os.dup(stderr_fd), 'wb') as copied:
        stderr.flush()  # flush library buffers that dup2 knows nothing about
        try:
            os.dup2(fileno(to), stderr_fd)  # $ exec >&to
        except ValueError:  # filename
            with open(to, 'wb') as to_file:
                os.dup2(to_file.fileno(), stderr_fd)  # $ exec > to
        try:
            yield stderr  # allow code to be run with the redirected stdout
        finally:
            # restore stdout to its previous value
            # NOTE: dup2 makes stdout_fd inheritable unconditionally
            stderr.flush()
            os.dup2(copied.fileno(), stderr_fd)  # $ exec >&copied