import json
import logging

import webapp2

from rogerthat.dal.app import get_apps_by_id
from rogerthat.models import AppNameMapping


class AppleAppSiteAssociationHandler(webapp2.RequestHandler):

    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.headers['Cache-Control'] = 'max-age=3600, public'

        names_dict = {}
        for mapping in AppNameMapping.query():
            if mapping.app_id not in names_dict:
                names_dict[mapping.app_id] = []
            names_dict[mapping.app_id].append(mapping.name)

        app_dict = {app.app_id: app for app in get_apps_by_id(names_dict.keys())}

        data = {'applinks': {'details': []}}
        for app_id, names in names_dict.iteritems():
            app = app_dict.get(app_id)
            if not app:
                logging.error('AppleAppSiteAssociationHandler missing app for id -> %s', app_id)
                continue
            if not app.ios_dev_team:
                logging.error('AppleAppSiteAssociationHandler missing ios_dev_team for app -> %s', app.app_id)
                continue

            data['applinks']['details'].append({
                'appID': '%s.com.mobicage.rogerthat.%s' % (app.ios_dev_team, app.app_id),
                'paths': ['/web/%s/news/id/*' % name for name in names]
            })

        json.dump(data, self.response.out)
