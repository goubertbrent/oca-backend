from datetime import datetime
import logging

from rogerthat.bizz.job import run_job
from rogerthat.dal import parent_key
from rogerthat.models import ServiceCallBackConfiguration, ServiceProfile,\
    ServiceCallBackSettings, ServiceCallBackConfig
from rogerthat.rpc import users


def migrate():
    run_job(_get_all_services, [], _move_to_one, [])

def cleanup():
    pass # todo cleanup ServiceCallBackConfiguration 


def _get_all_services():
    return ServiceProfile.all(keys_only=True)


def _move_to_one(profile_key):
    service_user = users.User(profile_key.parent().name())
    logging.debug(service_user)
    callback_settings = ServiceCallBackSettings(key=ServiceCallBackSettings.create_key(service_user), configs=[])
    for old_config in ServiceCallBackConfiguration.all().ancestor(parent_key(service_user)):
        if not old_config.regex:
            continue
        d = datetime.utcfromtimestamp(old_config.creationTime)
        config = ServiceCallBackConfig(created=d,
                                       updated=d,
                                       name=old_config.name,
                                       uri=old_config.callBackURI,
                                       regexes=[old_config.regex],
                                       callbacks=-1,
                                       custom_headers=None)
        callback_settings.configs.append(config)
    if callback_settings.configs:
        callback_settings.put()
    