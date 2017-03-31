# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# @@license_version:1.3@@

import json
import logging
import uuid
from contextlib import closing
from types import NoneType

from google.appengine.ext import db, deferred

from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from mcfw.utils import chunks
from rogerthat.bizz.friends import breakFriendShip, makeFriends
from rogerthat.bizz.job import run_job
from rogerthat.bizz.profile import create_user_profile, update_password_hash
from rogerthat.bizz.service import remove_service_identity_from_index, re_index, get_shorturl_for_qr
from rogerthat.consts import HIGH_LOAD_CONTROLLER_QUEUE, MIGRATION_QUEUE
from rogerthat.dal import parent_key, put_and_invalidate_cache, parent_key_unsafe
from rogerthat.dal.profile import _get_profile_not_cached, get_service_profile, is_trial_service, get_user_profile, \
    get_profile_info
from rogerthat.dal.service import get_all_service_friend_keys_query, get_service_identities_query, \
    get_default_service_identity_not_cached
from rogerthat.models import ServiceProfile, App, ServiceIdentity, UserData, TrialServiceAccount, \
    MessageFlowRunRecord, SIKKey, APIKey, Branding, ServiceInteractionDef, ShortURL, ProfilePointer, Avatar, \
    UserProfile
from rogerthat.models.properties.keyvalue import KeyValueProperty, KVStore, KVBucket, KVBlobBucket
from rogerthat.models.utils import copy_model_properties
from rogerthat.rpc import users
from rogerthat.rpc.models import Session
from rogerthat.rpc.service import BusinessException
from rogerthat.utils import channel, bizz_check, now
from rogerthat.utils.service import create_service_identity_user, get_service_user_from_service_identity_user, \
    get_identity_from_service_identity_user
from rogerthat.utils.transactions import on_trans_committed, run_in_xg_transaction
from shop.bizz import re_index_customer
from solutions.common.bizz import SolutionModule
from solutions.common.bizz.provisioning import put_qr_codes, populate_identity, create_calendar_admin_qr_code, \
    create_inbox_forwarding_qr_code, put_loyalty, create_inbox_forwarding_flow
from solutions.common.dal import get_solution_settings, get_solution_main_branding, get_solution_identity_settings
from solutions.common.dal.cityapp import invalidate_service_user_for_city
from solutions.common.models import SolutionQR, SolutionMainBranding, SolutionLogo, SolutionAvatar
from solutions.common.models.agenda import EventReminder, SolutionCalendar
from solutions.common.models.loyalty import SolutionLoyaltySettings, SolutionLoyaltyIdentitySettings
from solutions.common.models.reservation import RestaurantReservation, RestaurantProfile
from solutions.common.utils import create_service_identity_user_wo_default, is_default_service_identity

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class MigrateServiceJob(db.Model):
    # Caution: Populate PHASES at the bottom of the file when adding a new phase
    PHASE_1000_DISABLE_OLD_SERVICE = 1000
    PHASE_2000_MIGRATE_USER_DATA = 2000
    PHASE_2250_CLEANUP_USER_DATA = 2250
    PHASE_2500_MIGRATE_SERVICE_DATA = 2500
    PHASE_3000_REVOKE_ROLES = 3000
    PHASE_4000_DISCONNECT_FRIENDS = 4000
    PHASE_4500_MIGRATE_QRS = 4500
    PHASE_5000_MIGRATE_NON_ANCESTOR_MODELS = 5000
    PHASE_6000_MIGRATE_ANCESTOR_MODELS = 6000
    PHASE_7000_MIGRATE_SOLUTION = 7000
    PHASE_8000_FINISH_MODELS = 8000
    PHASE_9000_RECONNECT_FRIENDS = 9000
    PHASE_DONE = -1
    # Caution: Populate PHASES at the bottom of the file when adding a new phase

    executor_user = db.UserProperty(indexed=False, required=True)
    from_service_user = db.UserProperty(indexed=True, required=True)
    to_service_user = db.UserProperty(indexed=True, required=True)
    phase = db.IntegerProperty(indexed=True, required=True)
    start_timestamp = db.IntegerProperty(indexed=False, required=True)
    end_timestamp = db.IntegerProperty(indexed=False)

    fsic_keys = db.StringListProperty(indexed=False)
    solution = db.StringProperty(indexed=False)
    customer_key = db.StringProperty(indexed=False)
    service_enabled = db.BooleanProperty(indexed=False)
    service_grants = db.TextProperty()  # JSON string: { app_user : { si_user : [roles] } }
    data = KeyValueProperty()  # { app_user : { si_user : user_data } }

    @classmethod
    def get_sorted_phases(cls):
        return sorted((getattr(cls, attr) for attr in dir(cls) if attr.startswith('PHASE_')),
                      key=lambda x: (int(x == cls.PHASE_DONE), x))  # DONE positioned at the end

    def estimate_progress(self):
        if self.phase is None:
            return 0

        phases = self.get_sorted_phases()
        try:
            current_phase_index = phases.index(self.phase)
        except:
            for i, p in enumerate(phases):
                if p == self.PHASE_DONE:
                    continue
                if self.phase > p:
                    current_phase_index = max(0, i - 1)

        return max(1.0, 100.0 * current_phase_index / (len(phases) - 1))  # return minimum 1%

    def add_service_grant(self, si_user, app_user, role):
        # { app_user : { si_user : [roles] } }
        grants_dict = self.get_service_grants()
        app_user_grants = grants_dict.setdefault(app_user.email(), dict())
        roles = app_user_grants.setdefault(si_user.email(), list())
        roles.append(role)
        self.service_grants = json.dumps(grants_dict)

    def get_service_grants(self):
        return json.loads(self.service_grants) if self.service_grants else dict()

    def set_user_datas(self, user_datas):
        with closing(StringIO()) as stream:
            json.dump(user_datas, stream)
            self.data[u'user_datas'] = stream

    def get_user_datas(self):
        return self.data and self.data.get(u'user_datas') or dict()


@returns(ServiceProfile)
@arguments(from_service_user=users.User, to_service_user=users.User)
def _validate_job(from_service_user, to_service_user):
    # FROM != TO
    bizz_check(from_service_user.email() != to_service_user.email(),
               'FROM and TO should not be equal')

    # FROM should exist and be a ServiceProfile
    from_service_profile = _get_profile_not_cached(from_service_user)
    bizz_check(from_service_profile,
               'ServiceProfile %s not found' % from_service_user)
    bizz_check(isinstance(from_service_profile, ServiceProfile),
               'Profile %s is not of expected type ServiceProfile, but of type %s' % (from_service_user,
                                                                                      from_service_profile.kind()))

    # TO should not exist
    to_profile = _get_profile_not_cached(to_service_user)
    if to_profile:
        raise BusinessException('%s %s already exists' % (to_profile.kind(), to_service_user))

    # FROM should not be an auto_connected_service in an App
    for app in App.all():
        if from_service_user.email() in app.admin_services:
            raise BusinessException('FROM should not be an app admin service (found in app %s)' % app.app_id)

        for acs in app.auto_connected_services:
            acs_si_user = users.User(acs.service_identity_email)
            if get_service_user_from_service_identity_user(acs_si_user).email() == from_service_user.email():
                raise BusinessException('FROM should not be an AutoConnectedService (found %s in app %s)'
                                        % (acs_si_user, app.app_id))

    # Validate that there are no running jobs for <from_service> or <to_service>
    def get_base_query():
        return MigrateServiceJob.all().filter('phase !=', MigrateServiceJob.PHASE_DONE)

    for service_user in (from_service_user, to_service_user):
        for prop in ('from_service_user', 'to_service_user'):
            job = get_base_query().filter(prop, service_user).get()
            if job:
                raise BusinessException('There already is a MigrateServiceJob with %s=%s\n%s'
                                        % (prop, service_user, db.to_dict(job)))

    return from_service_profile


@returns(MigrateServiceJob)
@arguments(job_key=db.Key, phase=(int, NoneType))
def _get_job(job_key, phase=None):
    def trans():
        job = db.get(job_key)

        bizz_check(job, "Job with key %s not found!" % job_key)
        if phase is not None:
            bizz_check(job.phase == phase,
                       "Expected job %s to be in phase %s, but the phase was %s" % (job_key, phase, job.phase))
        return job

    return trans() if db.is_in_transaction() else db.run_in_transaction(trans)


@returns(MigrateServiceJob)
@arguments(job_key=db.Key, phase=int, next_phase=int)
def _set_job_in_next_phase(job_key, phase, next_phase):
    def trans():
        job = _get_job(job_key, phase)
        job.phase = next_phase
        if next_phase == MigrateServiceJob.PHASE_DONE:
            job.end_timestamp = now()
        job.put()
        return job

    logging.info('Setting next phase (%s) for job %s', next_phase, job_key)
    return db.run_in_transaction(trans)


@returns()
@arguments(job=MigrateServiceJob)
def _log_progress(job):
    logging.info('Executing phase %s in migration of %s to %s (%i%%)',
                 job.phase, job.from_service_user, job.to_service_user, job.estimate_progress())


def _delete_sessions(service_user):
    keys = Session.all(keys_only=True).filter("user", service_user).fetch(4000)
    if keys:
        db.delete(keys)
        deferred.defer(_delete_sessions, service_user, _countdown=5)


def _delete_search_indexes(service_user):
    for si_key in ServiceIdentity.all(keys_only=True).ancestor(parent_key(service_user)):
        deferred.defer(remove_service_identity_from_index,
                       create_service_identity_user(service_user, si_key.name()), _queue=MIGRATION_QUEUE)


def _put_and_invalidate_cache_and_allocate_ids(*models):

    @db.non_transactional
    def _allocate_non_transactional():
        _allocate()

    def _allocate():
        from google.appengine.api import datastore
        datastore._GetConnection()._reserve_keys([m.key() for m in models if m.key().id() is not None])

    put_and_invalidate_cache(*models)
    if db.is_in_transaction():
        _allocate_non_transactional()
    else:
        _allocate()

def _1000_disable_old_service(job_key):
    phase = MigrateServiceJob.PHASE_1000_DISABLE_OLD_SERVICE
    next_phase = MigrateServiceJob.PHASE_2000_MIGRATE_USER_DATA

    # Validate that the job still exists
    job = _get_job(job_key, phase)

    # Do the work
    _log_progress(job)

    logging.info("1/ Set enabled=False")
    from_service_profile = get_service_profile(job.from_service_user)
    if from_service_profile.enabled:
        from_service_profile.enabled = False
        from_service_profile.solution = None
        from_service_profile.put()

    logging.info("2/ Drop search indexes asynchronously")
    _delete_search_indexes(job.from_service_user)

    logging.info("3/ Delete Sessions asynchronously")
    _delete_sessions(job.from_service_user)

    # Set the next phase
    _set_job_in_next_phase(job_key, phase, next_phase)


def _2000_migrate_user_data(job_key):
    phase = MigrateServiceJob.PHASE_2000_MIGRATE_USER_DATA
    next_phase = MigrateServiceJob.PHASE_2250_CLEANUP_USER_DATA

    # Validate that the job still exists
    job = _get_job(job_key, phase)

    # Do the work
    _log_progress(job)

    # Get all the UserData models (possibly contains None)
    user_data_keys = list()
    for fsic_str_key in job.fsic_keys:
        fsic_key = db.Key(fsic_str_key)
        app_user = users.User(fsic_key.parent().name())
        old_si_user = users.User(fsic_key.name())
        user_data_keys.append(UserData.createKey(app_user, old_si_user))

    if user_data_keys:
        # { app_user : { si_user : user_data } }
        job_user_datas = dict()
        for chunk in chunks(user_data_keys, 200):
            for user_data in db.get(chunk):
                if user_data:
                    app_user_datas = job_user_datas.setdefault(user_data.app_user.email(), dict())
                    if user_data.data:
                        app_user_datas[user_data.service_identity_user.email()] = user_data.data
                    elif user_data.userData:
                        app_user_datas[user_data.service_identity_user.email()] = json.dumps(user_data.userData.to_json_dict())

        if job_user_datas:
            logging.info("Storing job.user_datas: %s", job_user_datas)
            def trans_update_user_datas():
                job = _get_job(job_key)
                job.set_user_datas(job_user_datas)
                job.put()
            db.run_in_transaction(trans_update_user_datas)

    # Set the next phase
    _set_job_in_next_phase(job_key, phase, next_phase)


def _2250_cleanup_user_data(job_key):
    phase = MigrateServiceJob.PHASE_2250_CLEANUP_USER_DATA
    next_phase = MigrateServiceJob.PHASE_2500_MIGRATE_SERVICE_DATA

    # Validate that the job still exists
    job = _get_job(job_key, phase)
    _log_progress(job)

    # Do the work
    user_data_keys = list()
    for fsic_str_key in job.fsic_keys:
        fsic_key = db.Key(fsic_str_key)
        app_user = users.User(fsic_key.parent().name())
        old_si_user = users.User(fsic_key.name())
        user_data_keys.append(UserData.createKey(app_user, old_si_user))

    db.delete(user_data_keys)

    # Set the next phase
    _set_job_in_next_phase(job_key, phase, next_phase)


def _2500_migrate_service_data(job_key, si_keys=None):
    phase = MigrateServiceJob.PHASE_2500_MIGRATE_SERVICE_DATA
    next_phase = MigrateServiceJob.PHASE_3000_REVOKE_ROLES

    # Validate that the job still exists
    job = _get_job(job_key, phase)
    _log_progress(job)

    # Do the work
    if si_keys is None:
        si_keys = list(get_service_identities_query(job.from_service_user, keys_only=True))

    if si_keys:
        si_keys_chunk = list()
        while si_keys and len(si_keys_chunk) < 200:
            si_keys_chunk.append(si_keys.pop(0))

        def trans():
            si_chunk = db.get(si_keys_chunk)
            for si in reversed(si_chunk):
                if not si.serviceData:
                    si_chunk.remove(si)
                    continue
                old_ancestor = si.serviceData._ancestor
                new_ancestor = _create_new_key(job, si.serviceData._ancestor)
                for chunk in chunks(si.serviceData._keys.values(), 5):
                    _migrate_models(job, db.get([KVBucket.create_key(bucket_id, old_ancestor)
                                                 for bucket_id in chunk]))
                for chunk in chunks(si.serviceData._blob_keys.values(), 5):
                    for blob_bucket_ids in chunk:
                        _migrate_models(job, db.get([KVBlobBucket.create_key(blob_bucket_id, old_ancestor)
                                                     for blob_bucket_id in blob_bucket_ids]))
                si.serviceData._ancestor = new_ancestor
            if si_chunk:
                put_and_invalidate_cache(*si_chunk)

            if si_keys:
                # there is still work to do
                deferred.defer(_2500_migrate_service_data, job_key, si_keys,
                               _transactional=True, _queue=MIGRATION_QUEUE)
                return False
            return True

        done = run_in_xg_transaction(trans)
    else:
        done = True

    if done:
        # Set the next phase
        _set_job_in_next_phase(job_key, phase, next_phase)


def _3000_revoke_roles(job_key):
    phase = MigrateServiceJob.PHASE_3000_REVOKE_ROLES
    next_phase = MigrateServiceJob.PHASE_4000_DISCONNECT_FRIENDS

    # Validate that the job still exists
    job = _get_job(job_key, phase)

    # Do the work
    _log_progress(job)

    try:
        si_user_email = job.from_service_user.email()
        profiles = UserProfile.list_by_service_role_email(si_user_email)
        for p in profiles:
            def trans():
                job = db.get(job_key)

                for si_email, granted_roles in p.grants.iteritems():
                    if si_email.startswith(si_user_email + '/'):
                        si_user = users.User(si_email)
                        for role in granted_roles:
                            p.revoke_role(si_user, role)
                            job.add_service_grant(si_user, p.user, role)
                put_and_invalidate_cache(p, job)

            xg_on = db.create_transaction_options(xg=True)
            db.run_in_transaction_options(xg_on, trans)
    except BusinessException as e:
        logging.exception("Caught BusinessException")
        azzert(False, "Caught BusinessException: %s" % e)

    # Set the next phase
    _set_job_in_next_phase(job_key, phase, next_phase)


def _break_friends(fsic_key):
    breakFriendShip(users.User(fsic_key.parent().name()), users.User(fsic_key.name()))


def _4000_disconnect_friends(job_key, initial_run=True):
    phase = MigrateServiceJob.PHASE_4000_DISCONNECT_FRIENDS
    next_phase = MigrateServiceJob.PHASE_4500_MIGRATE_QRS

    # Validate that the job still exists
    job = _get_job(job_key, phase)

    # Do the work
    if initial_run:
        _log_progress(job)
        # Schedule breakup
        run_job(get_all_service_friend_keys_query, [job.from_service_user],
                _break_friends, [])
    else:
        # Check the friend count
        if not get_all_service_friend_keys_query(job.from_service_user).get():
            # Set the next phase
            _set_job_in_next_phase(job_key, phase, next_phase)
            return

    # Poll until there are no friends anymore
    deferred.defer(_4000_disconnect_friends, job_key, initial_run=False,
                   _countdown=5, _queue=HIGH_LOAD_CONTROLLER_QUEUE)


@returns([ServiceInteractionDef])
@arguments(job=MigrateServiceJob, old_sids=[ServiceInteractionDef])
def _migrate_sids(job, old_sids):
    @db.non_transactional
    def put_new_short_urls(new_sids):
        new_short_urls = [get_shorturl_for_qr(job.to_service_user, new_sid.key().id())[0]
                          for new_sid in new_sids]
        _put_and_invalidate_cache_and_allocate_ids(*new_short_urls)
        return new_short_urls

    @db.non_transactional
    def delete_old_short_urls(old_sids):
        old_short_url_keys = [db.Key.from_path(ShortURL.kind(),
                                               ServiceInteractionDef.shortUrl.get_value_for_datastore(qr).id())
                              for qr in old_sids]
        db.delete(old_short_url_keys)


    new_sids = _migrate_models(job, old_sids, delete_old_models=False, put_new_models=True)
    new_short_urls = put_new_short_urls(new_sids)

    for new_sid, new_short_url in zip(new_sids, new_short_urls):
        new_sid.shortUrl = new_short_url
        old_qr_template_key = ServiceInteractionDef.qrTemplate.get_value_for_datastore(new_sid)
        if old_qr_template_key:
            new_sid.qrTemplate = _create_new_key(job, old_qr_template_key)
    put_and_invalidate_cache(*new_sids)

    delete_old_short_urls(old_sids)
    db.delete(old_sids)
    return new_sids


def _4500_migrate_qrs(job_key):
    phase = MigrateServiceJob.PHASE_4500_MIGRATE_QRS
    next_phase = MigrateServiceJob.PHASE_5000_MIGRATE_NON_ANCESTOR_MODELS

    # Validate that the job still exists
    job = _get_job(job_key, phase)

    # Do the work
    _log_progress(job)


    logging.info("1/ Migrate recommendation QR codes")
    def trans_migrate_recommend_qrs():
        # Get SIs with recommend enabled
        service_identities = [si for si in get_service_identities_query(job.from_service_user) if si.shareSIDKey]
        if service_identities:
            old_sid_keys = map(db.Key, [si.shareSIDKey for si in service_identities])
            old_sid_keys = [k for k in old_sid_keys if k.parent().name() != job.to_service_user.email()]
            logging.info('Old recommendation QR codes: %s', old_sid_keys)
            if old_sid_keys:
                old_sids = db.get(old_sid_keys)

                new_sids = _migrate_sids(job, old_sids)
                for si, new_sid in zip(service_identities, new_sids):
                    si.shareSIDKey = str(new_sid.key())
                put_and_invalidate_cache(*service_identities)
                logging.info('New recommendation QR codes: %s', [new_sid.key() for new_sid in new_sids])
        else:
            logging.debug("No ServiceIdentity with recommendation enabled")

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans_migrate_recommend_qrs)


    logging.info("2/ Migrate all other QR codes")
    qry = ServiceInteractionDef.all().ancestor(parent_key(job.from_service_user))

    def trans_migrate_other_qrs():
        old_sids = qry.fetch(100)
        if not old_sids:
            return False

        _migrate_sids(job, old_sids)
        return True

    while db.run_in_transaction_options(xg_on, trans_migrate_other_qrs):
        pass  # run trans until it returns False


    logging.info("3/ Migrate all ProfilePointers")
    old_pp_keys = list()
    new_pps = list()
    for si_key in get_service_identities_query(job.from_service_user, keys_only=True):
        identity = si_key.name()
        old_si_user = create_service_identity_user(job.from_service_user, identity)
        new_si_user = create_service_identity_user(job.to_service_user, identity)
        old_pp_keys.append(ProfilePointer.create_key(old_si_user))
        new_pps.append(ProfilePointer.create(new_si_user))

    put_and_invalidate_cache(*new_pps)
    db.delete(old_pp_keys)

    # Set the next phase
    _set_job_in_next_phase(job_key, phase, next_phase)


def _5000_migrate_non_ancestor_models(job_key):
    phase = MigrateServiceJob.PHASE_5000_MIGRATE_NON_ANCESTOR_MODELS
    next_phase = MigrateServiceJob.PHASE_6000_MIGRATE_ANCESTOR_MODELS

    # Validate that the job still exists
    job = _get_job(job_key, phase)

    # Do the work
    _log_progress(job)

    models = list()
    logging.debug("1/ Collecting TrialServiceAccounts")
    for model in TrialServiceAccount.all().filter("service", job.from_service_user):
        model.service = job.to_service_user
        models.append(model)

    logging.info("2/ Collecting MessageFlowRunRecords")
    for model in MessageFlowRunRecord.all().filter("service_identity >=", job.from_service_user.email() + '/').filter("service_identity <", job.from_service_user.email() + u"/\ufffd"):
        identity = get_identity_from_service_identity_user(users.User(model.service_identity))
        model.service_identity = create_service_identity_user(job.to_service_user, identity).email()
        models.append(model)

    logging.info("3/ Collecting Avatar, Branding, SIKKey, APIKey")
    for model_class in (Avatar, Branding, SIKKey, APIKey):
        for model in model_class.all().filter("user", job.from_service_user):
            model.user = job.to_service_user
            models.append(model)

    logging.info('Putting %s non-ancestor models', len(models))
    _put_and_invalidate_cache_and_allocate_ids(*models)

    # Set the next phase
    _set_job_in_next_phase(job_key, phase, next_phase)


def _create_new_key(job, old_key):
    old_parent_key = old_key.parent()
    if old_parent_key:
        new_parent_key = _create_new_key(job, old_parent_key)
    else:
        new_parent_key = None

    old_key_name = old_key.name()
    if old_key_name:
        if old_key_name == job.from_service_user.email():
            new_key_id_or_name = job.to_service_user.email()
        elif old_key_name.startswith(job.from_service_user.email() + '/'):
            new_key_id_or_name = job.to_service_user.email() + old_key_name[len(job.from_service_user.email()):]
        else:
            new_key_id_or_name = old_key_name
    else:
        new_key_id_or_name = old_key.id_or_name()

    return db.Key.from_path(old_key.kind(), new_key_id_or_name, parent=new_parent_key)


def _migrate_models(job, old_models, delete_old_models=True, put_new_models=True):
    azzert(db.is_in_transaction())
    new_models = list()

    for old_model in old_models:
        kwargs = copy_model_properties(old_model)

        # Patch props of (ServiceMenuDef, ServiceInteractionDef), (Broadcast), (ServiceProfile)
        for prop in ['staticFlowKey', 'message_flow', 'editableTranslationSet']:
            old_prop = kwargs.get(prop)
            if old_prop:
                kwargs[prop] = str(_create_new_key(job, db.Key(old_prop)))

        new_model = old_model.__class__(key=_create_new_key(job, old_model.key()),
                                        **kwargs)
        new_models.append(new_model)

    if put_new_models:
        _put_and_invalidate_cache_and_allocate_ids(*new_models)
    if delete_old_models:
        db.delete(old_models)

    return new_models


def _migrate_ancestor_models(job, from_ancestor_key):
    def trans():
        old_models = db.GqlQuery("SELECT * WHERE ANCESTOR IS KEY('%s')" % str(from_ancestor_key)).fetch(None)
        if old_models:
            _migrate_models(job, old_models)
            return True
        return False
    xg_on = db.create_transaction_options(xg=True)
    while db.run_in_transaction_options(xg_on, trans):
        pass


def _6000_migrate_ancestor_models(job_key):
    phase = MigrateServiceJob.PHASE_6000_MIGRATE_ANCESTOR_MODELS
    next_phase = MigrateServiceJob.PHASE_7000_MIGRATE_SOLUTION

    # Validate that the job still exists
    job = _get_job(job_key, phase)

    # Do the work
    _log_progress(job)

    logging.info("1/ Migrating ServiceTranslationSet")
    _migrate_ancestor_models(job, parent_key(job.from_service_user, u'mc-i18n'))


    logging.info("2/ Migrating all other ancestor models")
    _migrate_ancestor_models(job, parent_key(job.from_service_user))


    # Set the next phase
    _set_job_in_next_phase(job_key, phase, next_phase)


def _7000_migrate_solution(job_key):
    phase = MigrateServiceJob.PHASE_7000_MIGRATE_SOLUTION
    next_phase = MigrateServiceJob.PHASE_8000_FINISH_MODELS

    # Validate that the job still exists
    job = _get_job(job_key, phase)

    # Do the work
    _log_progress(job)

    if job.solution:
        logging.info('0/ Migrate the solution models without ancestor, but with service_user as key name.')
        def trans0():
            new_models = list()
            old_models = list()

            for model_class in (SolutionMainBranding, SolutionLogo, SolutionAvatar):
                old_model = db.get(model_class.create_key(job.from_service_user))
                if old_model:
                    kwargs = copy_model_properties(old_model)
                    new_model = model_class(key=model_class.create_key(job.to_service_user),
                                            **kwargs)
                    new_models.append(new_model)
                    old_models.append(old_model)

            if new_models:
                put_and_invalidate_cache(*new_models)
            if old_models:
                db.delete(old_models)

        xg_on = db.create_transaction_options(xg=True)
        db.run_in_transaction_options(xg_on, trans0)

        old_sln_settings = get_solution_settings(job.from_service_user)
        identities = [None]
        if old_sln_settings.identities:
            identities.extend(old_sln_settings.identities)

        logging.info('1/ Migrate RestaurantReservations')
        for service_identity in identities:
            from_si_user = create_service_identity_user_wo_default(job.from_service_user, service_identity)
            to_si_user = create_service_identity_user_wo_default(job.to_service_user, service_identity)
            while True:
                reservations = RestaurantReservation.all().filter('service_user', from_si_user).fetch(300)
                if not reservations:
                    break
                for r in reservations:
                    r.service_user = to_si_user
                _put_and_invalidate_cache_and_allocate_ids(*reservations)


        logging.info('2/ Migrate EventReminders')
        for service_identity in identities:
            from_si_user = create_service_identity_user(job.from_service_user)
            to_si_user = create_service_identity_user(job.to_service_user)
            while True:
                reminders = EventReminder.all().filter('service_identity_user', from_si_user).fetch(300)
                if not reminders:
                    break
                for r in reminders:
                    r.service_identity_user = to_si_user
                _put_and_invalidate_cache_and_allocate_ids(*reminders)


        logging.info('3/ Migrate RestaurantProfile.reserve_flow_part2')
        restaurant_profile = db.get(RestaurantProfile.create_key(job.from_service_user))
        if restaurant_profile and restaurant_profile.reserve_flow_part2:
            old_part2_key = db.Key(restaurant_profile.reserve_flow_part2)
            new_part2_key = db.Key.from_path(old_part2_key.kind(), old_part2_key.id_or_name(),
                                             parent=parent_key(job.to_service_user))
            logging.debug('New key: %r', new_part2_key)
            restaurant_profile.reserve_flow_part2 = str(new_part2_key)
            _put_and_invalidate_cache_and_allocate_ids(restaurant_profile)


        logging.info('4/ Delete all SolutionQRs. They will be recreated when provisioning.')
        for service_identity in identities:
            service_identity_user = create_service_identity_user_wo_default(job.from_service_user, service_identity)
            db.delete(SolutionQR.all(keys_only=True).ancestor(parent_key_unsafe(service_identity_user, job.solution)))


        logging.info('5/ Delete Loyalty QR. It will be recreated when provisioning.')
        if SolutionModule.LOYALTY in old_sln_settings.modules:
            for service_identity in identities:
                if is_default_service_identity(service_identity):
                    loyalty_i_settings = db.get(SolutionLoyaltySettings.create_key(job.from_service_user))
                else:
                    loyalty_i_settings = db.get(SolutionLoyaltyIdentitySettings.create_key(job.from_service_user, service_identity))
                if loyalty_i_settings:
                    loyalty_i_settings.image_uri = None
                    loyalty_i_settings.content_uri = None
                    _put_and_invalidate_cache_and_allocate_ids(loyalty_i_settings)


        logging.info('6/ Change ancestor keys of solution models.')
        for solution in ['common', job.solution]:
            for service_identity in identities:
                if is_default_service_identity(service_identity):
                    _migrate_ancestor_models(job, parent_key(job.from_service_user, solution))
                else:
                    service_identity_user = create_service_identity_user_wo_default(job.from_service_user, service_identity)
                    _migrate_ancestor_models(job, parent_key_unsafe(service_identity_user, solution))


        sln_settings = get_solution_settings(job.to_service_user)
        sln_main_branding = get_solution_main_branding(job.to_service_user)
        users.set_user(job.to_service_user)
        try:
            populate_identity(sln_settings, sln_main_branding.branding_key, sln_main_branding.branding_key)
        finally:
            users.clear_user()

    # Set the next phase
    _set_job_in_next_phase(job_key, phase, next_phase)


def _re_index_service_identity(si_key):
    service_user = users.User(si_key.parent().name())
    si_user = create_service_identity_user(service_user, si_key.name())
    re_index(si_user)


def _8000_finish_models(job_key):
    phase = MigrateServiceJob.PHASE_8000_FINISH_MODELS
    next_phase = MigrateServiceJob.PHASE_9000_RECONNECT_FRIENDS

    # Validate that the job still exists
    job = _get_job(job_key, phase)

    # Do the work
    _log_progress(job)

    try:
        logging.info("1/ re_index all service identities asynchronously")
        if not is_trial_service(job.to_service_user):
            run_job(get_service_identities_query, [job.to_service_user, True],
                    _re_index_service_identity, [])

        logging.info("2/ set solution and enabled on the new ServiceProfile")
        def trans2():
            to_service_profile = get_service_profile(job.to_service_user)
            to_service_profile.enabled = job.service_enabled
            to_service_profile.solution = job.solution
            to_service_profile.put()
        db.run_in_transaction(trans2)

        logging.info("3/ couple the service to the customer")
        if job.customer_key:
            def trans3():
                customer = db.get(job.customer_key)
                customer.service_email = job.to_service_user.email()
                customer.migration_job = None
                customer.put()

                deferred.defer(re_index_customer, db.Key(job.customer_key),
                               _queue=MIGRATION_QUEUE, _transactional=True)
            db.run_in_transaction(trans3)
        else:
            logging.debug('There was no customer')

        logging.info("4/ grant service roles")
        service_grants = job.get_service_grants()  # { app_user : { si_user : [roles] } }
        for app_user_email, service_grant_dict in service_grants.iteritems():
            def trans4():
                p = get_user_profile(users.User(app_user_email), cached=False)
                for old_si_email, service_roles in service_grant_dict.iteritems():
                    old_si_user = users.User(old_si_email)
                    new_si_user = create_service_identity_user(job.to_service_user,
                                                               get_identity_from_service_identity_user(old_si_user))
                    for role in service_roles:
                        logging.debug("Granting role %s to %s for %s", role, app_user_email, new_si_user)
                        p.grant_role(new_si_user, role)
                p.put()
            db.run_in_transaction(trans4)

        logging.debug("5/ finish solution models")
        if job.solution:
            sln_settings = get_solution_settings(job.to_service_user)
            main_branding = get_solution_main_branding(job.to_service_user)
            users.set_user(job.to_service_user)
            try:
                if SolutionModule.LOYALTY in sln_settings.modules:
                    logging.debug('- Provisioning %s', SolutionModule.LOYALTY)
                    put_loyalty(sln_settings, None, main_branding, sln_settings.main_language, None)

                if SolutionModule.QR_CODES in sln_settings.modules:
                    logging.debug('- Provisioning %s', SolutionModule.QR_CODES)
                    put_qr_codes(sln_settings, None, main_branding, sln_settings.main_language, None)

                logging.debug('- Creating QR codes for calendar admins')
                calendars_to_put = []
                for sc in SolutionCalendar.all().ancestor(parent_key(sln_settings.service_user, sln_settings.solution)).filter("deleted =", False):
                    qr_code = create_calendar_admin_qr_code(sc, main_branding.branding_key, sln_settings.main_language)
                    sc.connector_qrcode = qr_code.image_uri
                    calendars_to_put.append(sc)
                if calendars_to_put:
                    db.put(calendars_to_put)

                logging.debug('- Creating QR codes for inbox forwarding')
                flow_identifier = create_inbox_forwarding_flow(main_branding.branding_key, sln_settings.main_language)
                qrcode = create_inbox_forwarding_qr_code(None, flow_identifier)
                sln_settings.inbox_connector_qrcode = qrcode.image_uri
                if sln_settings.identities:
                    for service_identity in sln_settings.identities:
                        qrcode = create_inbox_forwarding_qr_code(service_identity, flow_identifier)
                        def trans():
                            sln_i_settings = get_solution_identity_settings(sln_settings.service_user, service_identity)
                            sln_i_settings.inbox_connector_qrcode = qrcode.image_uri
                            sln_i_settings.put()
                        db.run_in_transaction(trans)
                put_and_invalidate_cache(sln_settings)
            finally:
                users.clear_user()
        else:
            logging.debug("The service was not a solution")
    except BusinessException, e:
        logging.exception("Caught BusinessException")
        azzert(False, "Caught BusinessException: %s" % e)

    logging.debug("6/ update owning user profiles")

    up_to_put = []
    for up in UserProfile.all().filter("owningServiceEmails =", job.from_service_user.email()):
        if job.from_service_user.email() in up.owningServiceEmails:
            up.owningServiceEmails.remove(job.from_service_user.email())
        if job.to_service_user.email() not in up.owningServiceEmails:
            up.owningServiceEmails.append(job.to_service_user.email())
        up_to_put.append(up)

    if up_to_put:
        put_and_invalidate_cache(*up_to_put)

    # Set the next phase
    _set_job_in_next_phase(job_key, phase, next_phase)


def _make_friends(job_key, app_user, si_user, fsic_str_key=None):
    profile_info = get_profile_info(app_user)
    if not isinstance(profile_info, UserProfile):
        logging.warn("%s was no UserProfile but %s", app_user.email(), profile_info)
        def trans():
            job = db.get(job_key)
            job.fsic_keys.remove(fsic_str_key)
            job.put()
        db.run_in_transaction(trans)
        return

    user_data_str = None
    job = db.get(job_key)
    if job:
        user_datas = job.get_user_datas()
        # { app_user : { si_user : user_data } }
        user_datas_for_app_user = user_datas.get(app_user.email())
        if user_datas_for_app_user is not None:
            old_si_user = create_service_identity_user(job.from_service_user,
                                                       get_identity_from_service_identity_user(si_user))
            user_data_str = user_datas_for_app_user.get(old_si_user.email())

    makeFriends(si_user, app_user, original_invitee=None, servicetag=None, origin=None, notify_invitee=False,
                notify_invitor=False, user_data=user_data_str)


def _9000_reconnect_friends(job_key, initial_run=True):
    phase = MigrateServiceJob.PHASE_9000_RECONNECT_FRIENDS
    next_phase = MigrateServiceJob.PHASE_DONE

    # Validate that the job still exists
    job = _get_job(job_key, phase)

    # Do the work
    if initial_run:
        _log_progress(job)
        # Schedule breakup
        for fsic_str_key in job.fsic_keys:
            fsic_key = db.Key(fsic_str_key)
            app_user = users.User(fsic_key.parent().name())
            old_si_user = users.User(fsic_key.name())
            new_si_user = create_service_identity_user(job.to_service_user,
                                                     get_identity_from_service_identity_user(old_si_user))
            deferred.defer(_make_friends, job_key, app_user, new_si_user, fsic_str_key, _queue=MIGRATION_QUEUE)
    else:
        # Check the friend count
        current_friend_count = get_all_service_friend_keys_query(job.to_service_user).count(limit=None)
        expected_friend_count = len(job.fsic_keys)
        logging.info('Friend count: %s/%s', current_friend_count, expected_friend_count)
        if current_friend_count == expected_friend_count:
            # Set the next phase
            _set_job_in_next_phase(job_key, phase, next_phase)
            return

    deferred.defer(_9000_reconnect_friends, job_key, False,
                   _countdown=5, _queue=HIGH_LOAD_CONTROLLER_QUEUE)


def controller(job_key, current_phase=None, retry_interval=0):
    '''Responsible for chaining the different phases'''
    job = _get_job(job_key)
    logging.debug('MigrateServiceJob phase %s->%s (key %s)', current_phase, job.phase, job_key)

    if job.phase == MigrateServiceJob.PHASE_DONE:
        logging.info('Migration of %s to %s completed!', job.from_service_user, job.to_service_user)
        return

    if job.phase == current_phase:
        next_retry_interval = min(retry_interval + 1, 5)
    else:
        worker = PHASES.get(job.phase)
        azzert(worker, 'Unexpected job phase: %s' % job.phase)

        kwargs = dict(job_key=job_key, _queue=MIGRATION_QUEUE)
        deferred.defer(worker, **kwargs)
        channel.send_message(job.executor_user, 'rogerthat.jobs.migrate_service.next_phase',
                             progress=job.estimate_progress(),
                             phase=job.phase)

        next_retry_interval = 1

    deferred.defer(controller, job_key, job.phase, next_retry_interval,
                   _countdown=next_retry_interval, _queue=HIGH_LOAD_CONTROLLER_QUEUE)

@returns(MigrateServiceJob)
@arguments(executor_user=users.User, from_service_user=users.User, to_user=users.User)
def migrate_and_create_user_profile(executor_user, from_service_user, to_user):
    from shop.models import Customer
    bizz_check(from_service_user.email() != to_user.email(), 'FROM and TO should not be equal')

    from_profile = _get_profile_not_cached(from_service_user)
    bizz_check(from_profile, 'ServiceProfile %s not found' % from_service_user)
    bizz_check(isinstance(from_profile, ServiceProfile),
               'Profile %s is not of expected type ServiceProfile, but of type %s' % (from_service_user, from_profile.kind()))

    service_email = u"service-%s@rogerth.at" % uuid.uuid4()

    to_profile = _get_profile_not_cached(to_user)
    if to_profile:
        bizz_check(isinstance(to_profile, UserProfile), 'Profile %s is not of expected type UserProfile, but of type %s' % (to_user, to_profile.kind()))
        if service_email not in to_profile.owningServiceEmails:
            to_profile.owningServiceEmails.append(service_email)
    else:
        to_profile = create_user_profile(to_user, to_user.email(), from_profile.defaultLanguage)
        to_profile.isCreatedForService = True
        to_profile.owningServiceEmails = [service_email]
        update_password_hash(to_profile, from_profile.passwordHash, now())

    si = get_default_service_identity_not_cached(from_service_user)
    si.qualifiedIdentifier = to_user.email()
    settings = get_solution_settings(from_service_user)
    settings.qualified_identifier = to_user.email()
    settings.login = to_user
    put_and_invalidate_cache(to_profile, si, settings)

    customer = Customer.all().filter('service_email', from_service_user.email()).get()
    if customer:
        def trans(customer_key):
            customer = db.get(customer_key)
            customer.user_email = to_user.email()
            customer.put()
        db.run_in_transaction(trans, customer.key())

        if SolutionModule.CITY_APP in settings.modules:
            for app_id in customer.app_ids:
                invalidate_service_user_for_city(app_id)
    else:
        logging.debug('There was no customer')

    return migrate(executor_user, from_service_user, users.User(service_email))

@returns(MigrateServiceJob)
@arguments(executor_user=users.User, from_service_user=users.User, to_service_user=users.User)
def migrate(executor_user, from_service_user, to_service_user):
    from shop.models import Customer
    from_service_profile = _validate_job(from_service_user, to_service_user)

    customer = Customer.all().filter('service_email', from_service_user.email()).get()
    fsic_keys = map(str, get_all_service_friend_keys_query(from_service_user))

    job_key = db.Key.from_path(MigrateServiceJob.kind(), str(uuid.uuid4()),
                               parent=db.Key.from_path(MigrateServiceJob.kind(), MigrateServiceJob.kind()))
    def trans():
        job = MigrateServiceJob(key=job_key,
                                executor_user=executor_user,
                                from_service_user=from_service_user,
                                to_service_user=to_service_user,
                                phase=MigrateServiceJob.PHASE_1000_DISABLE_OLD_SERVICE,
                                solution=from_service_profile.solution,
                                customer_key=str(customer.key()) if customer else None,
                                fsic_keys=fsic_keys,
                                service_enabled=from_service_profile.enabled,
                                start_timestamp=now(),
                                data=KVStore(job_key))
        job.put()

        if customer:
            customer.migration_job = str(job_key)
            customer.put()

        deferred.defer(controller, job_key, None,
                       _transactional=True, _queue=HIGH_LOAD_CONTROLLER_QUEUE)

        on_trans_committed(channel.send_message, from_service_user, u'rogerthat.system.dologout')

        return job

    xg_on = db.create_transaction_options(xg=True)
    return db.run_in_transaction_options(xg_on, trans)


PHASES = {MigrateServiceJob.PHASE_1000_DISABLE_OLD_SERVICE : _1000_disable_old_service,
          MigrateServiceJob.PHASE_2000_MIGRATE_USER_DATA : _2000_migrate_user_data,
          MigrateServiceJob.PHASE_2250_CLEANUP_USER_DATA: _2250_cleanup_user_data,
          MigrateServiceJob.PHASE_2500_MIGRATE_SERVICE_DATA : _2500_migrate_service_data,
          MigrateServiceJob.PHASE_3000_REVOKE_ROLES : _3000_revoke_roles,
          MigrateServiceJob.PHASE_4000_DISCONNECT_FRIENDS : _4000_disconnect_friends,
          MigrateServiceJob.PHASE_4500_MIGRATE_QRS : _4500_migrate_qrs,
          MigrateServiceJob.PHASE_5000_MIGRATE_NON_ANCESTOR_MODELS : _5000_migrate_non_ancestor_models,
          MigrateServiceJob.PHASE_6000_MIGRATE_ANCESTOR_MODELS : _6000_migrate_ancestor_models,
          MigrateServiceJob.PHASE_7000_MIGRATE_SOLUTION : _7000_migrate_solution,
          MigrateServiceJob.PHASE_8000_FINISH_MODELS : _8000_finish_models,
          MigrateServiceJob.PHASE_9000_RECONNECT_FRIENDS : _9000_reconnect_friends,
          MigrateServiceJob.PHASE_DONE : None,
          }
