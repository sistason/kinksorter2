import logging
from fuzzywuzzy import fuzz

from django.db.utils import ConnectionRouter

from kinksorter_app.apis.kinkcom.models import KinkComSite, KinkComShoot, KinkComPerformer
from kinksorter_app.apis.kinkcom.kink_api import KinkAPI


class APIRouter(ConnectionRouter):

    def db_for_read(self, model, **hints):
        if model in [KinkComSite, KinkComShoot, KinkComPerformer]:
            return 'API_kinkcom'
        else:
            return 'default'

    def db_for_write(self, model, **hints):
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Relations between objects are allowed if both objects are
        in the master/slave pool.
        """
        db_list = ('default')
        return obj1._state.db in db_list and obj2._state.db in db_list

    def allow_migrate(self, db, app_label, model_name='', model=None):
        """
        All non-auth models end up in this pool.
        """
        return True


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
