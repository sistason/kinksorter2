import logging
from fuzzywuzzy import fuzz

from kinksorter_app.apis.kinkcom.kink_api import KinkAPI


def get_correct_api(dir_name, apis):
    scores = []
    for name, api in apis.items():
        if api is None:
            continue

        responsibilities = api.get_site_responsibilities()
        for resp in responsibilities:
            score = fuzz.token_set_ratio(dir_name, resp)
            scores.append((score, api, resp))

    scores.sort(key=lambda f: f[0])
    if scores and scores[-1][0] > 85:
        return scores[-1][1]

    logging.warning('Found no suitable API for folder "{}". '
                    'Not yet supported or consider naming it more appropriate'.format(dir_name))
    return None


kink_api = KinkAPI()
APIS = {'Kink.com': kink_api, 'Default': kink_api}
