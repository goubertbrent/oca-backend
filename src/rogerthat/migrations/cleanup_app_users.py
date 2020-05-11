import logging

from rogerthat.bizz.job import run_job
from rogerthat.bizz.user import archiveUserDataAfterDisconnect
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.dal.friend import get_friends_map
from rogerthat.dal.roles import get_service_identities_via_user_roles
from rogerthat.models import UserProfile, App


def cleaunup_app_users(app_id, unregister_text):
    if app_id not in (App.APP_ID_ROGERTHAT,):
        return
    run_job(_get_profiles, [app_id], _cleanup_user_profile, [unregister_text], worker_queue=MIGRATION_QUEUE)


def _get_profiles(app_id):
    return UserProfile.list_by_app(app_id)


def _cleanup_user_profile(user_profile, unregister_reason):
    app_user = user_profile.user
    if user_profile.owningServiceEmails:
        logging.debug('_cleanup_user_profile failed user %s has %s owningServiceEmails', app_user, len(user_profile.owningServiceEmails))
        return

    service_identities = get_service_identities_via_user_roles(app_user)
    if service_identities:
        logging.debug('_cleanup_user_profile failed user %s manages %s service_identities', app_user, len(service_identities))
        return

    logging.debug('_cleanup_user_profile success user %s', app_user)
    friend_map = get_friends_map(app_user)
    archiveUserDataAfterDisconnect(app_user, friend_map, user_profile, hard_delete=True, unregister_reason=unregister_reason)