#!/usr/bin/env python3
from os import environ

import connexion
import logging
from google.cloud import logging as glogging
from google.cloud.logging.handlers.handlers import EXCLUDED_LOGGER_DEFAULTS

from oca.encoder import JSONEncoder
from oca.environment import PORT, DEBUG

all_excluded_loggers = list(EXCLUDED_LOGGER_DEFAULTS) + ['connexion', 'openapi_spec_validator',
                                                         'urllib3.connectionpool', 'werkzeug']
for excluded in all_excluded_loggers:
    logging.getLogger(excluded).setLevel(logging.INFO)

app = connexion.App(__name__, specification_dir='./oca/openapi/', options={'swagger_ui': True})
app.app.json_encoder = JSONEncoder
app.add_api('openapi.yaml',
            arguments={'title': 'Our City App'},
            pythonic_params=True,
            pass_context_arg_name='request')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
if not DEBUG:
    client = glogging.Client()
    logger.addHandler(client.get_default_handler())
    for logger_name in all_excluded_loggers:
        logger = logging.getLogger(logger_name)
        logger.propagate = False
        logger.addHandler(logging.StreamHandler())

if __name__ == '__main__':
    if not environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        raise Exception('You must set the GOOGLE_APPLICATION_CREDENTIALS environment variable')
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # See https://cloud.google.com/appengine/docs/standard/python3/runtime#environment_variables
    app.run(host='127.0.0.1', port=PORT, debug=DEBUG)
