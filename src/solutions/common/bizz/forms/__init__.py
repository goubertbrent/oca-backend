# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley Belgium NV
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
# @@license_version:1.7@@

import json
import logging
import random
from datetime import datetime
from os import path

import cloudstorage
import dateutil
from google.appengine.api.taskqueue import taskqueue
from google.appengine.datastore import datastore_rpc
from google.appengine.ext import ndb
from google.appengine.ext.deferred import deferred

from mcfw.consts import MISSING
from mcfw.imaging import recolor_png
from mcfw.rpc import arguments, returns
from rogerthat.bizz.gcs import get_serving_url
from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.consts import SCHEDULED_QUEUE, MC_RESERVED_TAG_PREFIX
from rogerthat.dal import parent_ndb_key
from rogerthat.dal.profile import get_profile_infos, get_user_profile, get_service_profile
from rogerthat.models import Message, ServiceIdentity
from rogerthat.rpc import users
from rogerthat.rpc.users import get_current_session
from rogerthat.service.api import system, messaging
from rogerthat.service.api.forms import service_api
from rogerthat.to.forms import DynamicFormTO, FormSubmittedCallbackResultTO, \
    SubmitDynamicFormRequestTO, FormSectionValueTO
from rogerthat.to.messaging import MemberTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import try_or_defer, parse_color
from rogerthat.utils.app import create_app_user_by_email
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks
from solutions import translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import broadcast_updates_pending, get_next_free_spot_in_service_menu
from solutions.common.bizz.forms.integrations import get_form_integration
from solutions.common.bizz.forms.statistics import get_all_statistic_keys, update_form_statistics, get_form_statistics, \
    remove_submission_from_shard, get_random_shard_number
from solutions.common.bizz.forms.util import remove_sensitive_answers
from solutions.common.consts import OCA_FILES_BUCKET
from solutions.common.dal import get_solution_settings, get_solution_main_branding
from solutions.common.models import SolutionBrandingSettings
from solutions.common.models.forms import OcaForm, FormTombola, TombolaWinner, FormSubmission, FormStatisticsShard, \
    CompletedFormStep, CompletedFormStepType, FormIntegrationConfiguration, FormIntegration, FormIntegrationProvider
from solutions.common.to.forms import OcaFormTO, FormSettingsTO, FormStatisticsTO


def can_edit_integration_config():
    current_session = get_current_session()
    return current_session and current_session.shop


def list_forms(service_user):
    return OcaForm.list_by_user(service_user)


def create_form(data, service_user):
    # type: (OcaFormTO, users.User) -> OcaFormTO
    with users.set_user(service_user):
        created_form = service_api.create_form(data.form.title, data.form.sections, data.form.submission_section,
                                               data.form.max_submissions)
    oca_form = OcaForm(key=OcaForm.create_key(created_form.id, service_user))
    can_edit_integrations = can_edit_integration_config()
    _update_form(oca_form, created_form, data.settings, can_edit_integrations)
    if oca_form.visible:
        _create_form_menu_item(oca_form)
    return OcaFormTO(form=created_form, settings=FormSettingsTO.from_model(oca_form, can_edit_integrations))


def update_form(form_id, data, service_user):
    # type: (int, OcaFormTO, users.User) -> OcaFormTO
    can_edit_integrations = can_edit_integration_config()
    with users.set_user(service_user):
        if data.settings.tombola:
            data.form.max_submissions = 1
        oca_form = OcaForm.create_key(form_id, service_user).get()  # type: OcaForm
        visibility_changed = oca_form.visible != data.settings.visible
        # Form is readonly after it is finished
        if oca_form.finished:
            form = service_api.get_form(form_id)
            return OcaFormTO(form=form, settings=FormSettingsTO.from_model(oca_form, can_edit_integrations))
        for section in data.form.sections:
            if MISSING.default(section.branding, None) and section.branding.logo_url:
                section.branding.avatar_url = _get_form_avatar_url(service_user)
        updated_form = service_api.update_form(form_id, data.form.title, data.form.sections,
                                               data.form.submission_section, data.form.max_submissions)
        _delete_scheduled_task(oca_form)
        _update_form(oca_form, updated_form, data.settings, can_edit_integrations)
        if oca_form.visible:
            _create_form_menu_item(oca_form)
            if oca_form.visible_until:
                seconds_left = (oca_form.visible_until - datetime.now()).total_seconds()
                # cron to finish forms runs every hour, schedule the task now if the remaining time is less than that.
                if seconds_left < 3600:
                    task = create_task(finish_form, oca_form.id, oca_form.service_user, _countdown=seconds_left,
                                       _task_name=get_finish_form_task_name(updated_form))
                    schedule_tasks([task], SCHEDULED_QUEUE)
        else:
            _delete_form_menu_item(oca_form.id)
        settings = get_solution_settings(service_user)
        changed = False
        if visibility_changed:
            if settings.updates_pending:
                settings.updates_pending = False
                changed = True
            system.publish_changes()
        else:
            if not settings.updates_pending:
                settings.updates_pending = True
                changed = True
        if changed:
            settings.put()
            broadcast_updates_pending(settings)
    return OcaFormTO(form=updated_form, settings=FormSettingsTO.from_model(oca_form, can_edit_integrations))


def _update_form(model, created_form, settings, can_edit_integrations):
    # type: (OcaForm, DynamicFormTO, FormSettingsTO, bool) -> None
    model.populate(icon=settings.icon or OcaForm.icon._default,
                   visible=settings.visible,
                   visible_until=settings.visible_until and _get_utc_datetime(settings.visible_until),
                   tombola=settings.tombola and FormTombola(**settings.tombola.to_dict()),
                   steps=[CompletedFormStep(step_id=step.step_id) for step in settings.steps])
    if can_edit_integrations:
        model.integrations = [FormIntegration(provider=i.provider, enabled=i.enabled, configuration=i.configuration)
                              for i in settings.integrations]
    if created_form:
        model.populate(
            version=created_form.version,
            title=created_form.title,
        )
    model.put()
    service_profile = get_service_profile(model.service_user)
    integration_models = get_form_integrations(model.service_user)
    integration_configs = {i.provider: i for i in integration_models}
    for integration in model.integrations:
        if integration.enabled and integration.provider in integration_configs:
            conf = integration_configs[integration.provider]
            get_form_integration(integration.provider, conf).update_configuration(model.id, integration.configuration,
                                                                                  service_profile)


def _get_form_avatar_url(service_user):
    # type: (users.User) -> str
    branding_settings = SolutionBrandingSettings.get_by_user(service_user)  # type: SolutionBrandingSettings
    cloudstorage_path = '/%s/forms/avatars/list-%s.png' % (OCA_FILES_BUCKET, branding_settings.menu_item_color)
    try:
        cloudstorage.stat(cloudstorage_path)
    except cloudstorage.NotFoundError:
        with cloudstorage.open(cloudstorage_path, 'w', content_type='image/png') as gcs_file:
            with open(path.join(path.dirname(__file__), 'list.png')) as f:
                color = parse_color(branding_settings.menu_item_color)
                gcs_file.write(recolor_png(f.read(), (0, 0, 0), color))
    return get_serving_url(cloudstorage_path)


def get_form_settings(form_id, service_user):
    # type: (long, users.User) -> OcaForm
    return OcaForm.create_key(form_id, service_user).get()


def get_form(form_id, service_user):
    with users.set_user(service_user):
        form = service_api.get_form(form_id)
    oca_form = get_form_settings(form_id, service_user)
    # backwards compat
    if not oca_form.steps:
        oca_form.steps = [CompletedFormStep(step_id=step_id) for step_id in CompletedFormStepType.all()]
    return OcaFormTO(form=form, settings=FormSettingsTO.from_model(oca_form, can_edit_integration_config()))


@arguments(service_user=users.User, form_id=(int, long), cursor=unicode, page_size=(int, long))
def list_responses(service_user, form_id, cursor, page_size):
    # type: (users.User, int, unicode, int) -> list[FormSubmission]
    page_size = min(page_size, 1000)
    get_form(form_id, service_user)  # validate user
    return FormSubmission.list(form_id).fetch_page(page_size,
                                                   start_cursor=cursor and ndb.Cursor.from_websafe_string(cursor))


def delete_submission(service_user, form_id, submission_id):
    # type: (users.User, long, long) -> None
    submission = FormSubmission.create_key(submission_id).get()
    with users.set_user(service_user):
        service_api.delete_form_submission(form_id, submission.user)
    try_or_defer(_delete_submission, submission_id)


@ndb.transactional(xg=True)
def _delete_submission(submission_id):
    # type: (long) -> None
    submission = FormSubmission.create_key(submission_id).get()  # type: FormSubmission
    if submission.statistics_shard_id:
        shard = FormStatisticsShard.create_key(submission.statistics_shard_id).get()
        shard = remove_submission_from_shard(shard, submission)
        shard.put()
    submission.key.delete()


def delete_submissions(service_user, form_id):
    # type: (users.User, long) -> None
    get_form(form_id, service_user)
    with users.set_user(service_user):
        service_api.delete_form_submissions(form_id)
    _delete_form_submissions(form_id)


@returns(FormStatisticsTO)
@arguments(service_user=users.User, form_id=(int, long))
def get_statistics(service_user, form_id):
    # type: (users.User, int) -> FormStatisticsTO
    with users.set_user(service_user):
        form = service_api.get_form(form_id)
        return get_form_statistics(form)


def _get_utc_datetime(datetime_str):
    return dateutil.parser.parse(datetime_str, ignoretz=True)  # type: datetime


def _create_form_menu_item(form):
    from solutions.common.bizz.messaging import POKE_TAG_FORMS
    menu = system.get_menu()
    existing_item = None
    tag = json.dumps({
        '%s.tag' % MC_RESERVED_TAG_PREFIX: POKE_TAG_FORMS,
        'id': form.id
    }, sort_keys=True)
    for item in menu.items:
        if item.form:
            if item.form.id == form.id:
                existing_item = item
    if existing_item:
        new_coords = existing_item.coords
        # Don't overwrite tag in case we manually changed it to something else (to put it in the sidebar for example)
        tag = existing_item.tag
    else:
        all_taken_coords = [item.coords for item in menu.items]
        new_coords = get_next_free_spot_in_service_menu(all_taken_coords, 0)
    system.put_menu_item(form.icon, form.title, tag, new_coords, form_id=form.id)


def _delete_form_menu_item(form_id):
    # type: (int) -> bool
    menu = system.get_menu()
    has_deleted = False
    for item in menu.items:
        if item.form and item.form.id == form_id:
            system.delete_menu_item(item.coords)
            has_deleted = True
    return has_deleted


def _delete_scheduled_task(form):
    task_name = get_finish_form_task_name(form)
    taskqueue.Queue(SCHEDULED_QUEUE).delete_tasks_by_name([task_name])


def finish_form(form_id, service_user):
    return _finish_form(form_id, service_user)


@ndb.transactional()
def _finish_form(form_id, service_user):
    form = OcaForm.create_key(form_id, service_user).get()  # type: OcaForm
    if not form or form.finished:
        # Already deleted or set as invisible
        return
    form.visible = False
    form.finished = True
    if form.tombola:
        deferred.defer(_choose_tombola_winners, form.id, service_user, _transactional=True)
    form.put()
    deferred.defer(_delete_menu_item, form_id, service_user, _transactional=True)


def _delete_menu_item(form_id, service_user):
    with users.set_user(service_user):
        if _delete_form_menu_item(form_id):
            system.publish_changes()


def get_tombola_winners(form_id):
    # type: (int) -> list[UserDetailsTO]
    service_api.get_form(form_id)  # validate if user has permission
    user_emails = [users.User(winner.user) for winner in TombolaWinner.list_by_form_id(form_id)]
    return [UserDetailsTO.fromUserProfile(profile_info) for profile_info in get_profile_infos(user_emails)]


def _choose_tombola_winners(form_id, service_user):
    # type: (int, users.User) -> None
    form = OcaForm.create_key(form_id, service_user).get()  # type: OcaForm
    if TombolaWinner.list_by_form_id(form_id).count(1):
        logging.warning('Not re-picking winners for already finished tombola for form %s', form_id)
        return
    all_keys = FormSubmission.list(form_id).fetch(ndb.query._MAX_LIMIT, keys_only=True)
    key_count = len(all_keys)
    if not key_count:
        logging.debug('No participants for tombola %s :(', form_id)
        return
    max_index = key_count - 1
    random_keys = []
    while len(random_keys) < form.tombola.winner_count:
        index = random.randint(0, max_index)
        key = all_keys[index]
        if key not in random_keys:
            random_keys.append(key)
        elif len(random_keys) == key_count:
            # Not enough participants
            break
    winning_submissions = ndb.get_multi(random_keys)  # type: list[FormSubmission]
    parent = parent_ndb_key(service_user, SOLUTION_COMMON)
    to_put = [TombolaWinner(parent=parent, form_id=form.id, user=submission.user) for
              submission in winning_submissions]
    ndb.put_multi(to_put)
    main_branding = get_solution_main_branding(service_user)

    winners = [users.User(submission.user) for submission in winning_submissions]
    tasks = [create_task(_send_tombola_message, service_user, form.tombola.winner_message, MemberTO.from_user(winner),
                         main_branding.branding_key) for winner in winners]
    schedule_tasks(tasks)


def _send_tombola_message(service_user, message, member, branding_key):
    from solutions.common.bizz.messaging import POKE_TAG_FORM_TOMBOLA_WINNER
    with users.set_user(service_user):
        messaging.send(parent_key=None,
                       parent_message_key=None,
                       message=message,
                       answers=[],
                       flags=Message.FLAG_ALLOW_DISMISS,
                       members=[member],
                       branding=branding_key,
                       tag=POKE_TAG_FORM_TOMBOLA_WINNER,
                       service_identity=ServiceIdentity.DEFAULT)


def get_finish_form_task_name(form):
    return '%s-%s-%s' % (finish_form.__name__, form.id, form.version)


def delete_form(form_id, service_user):
    must_publish = _delete_form_menu_item(form_id)
    with users.set_user(service_user):
        service_api.delete_form(form_id)
    _delete_form_submissions(form_id)
    OcaForm.create_key(form_id, service_user).delete()
    if must_publish:
        system.publish_changes()


def _delete_form_submissions(form_id):
    run_job(_get_form_submissions, [form_id], _delete_submissions, [], mode=MODE_BATCH,
            batch_size=datastore_rpc.Connection.MAX_DELETE_KEYS)
    to_delete = get_all_statistic_keys(form_id)
    ndb.delete_multi(to_delete)


def _get_form_submissions(form_id):
    return FormSubmission.query(FormSubmission.form_id == form_id)


def _delete_submissions(submission_keys):
    ndb.delete_multi(submission_keys)


def create_form_submission(service_user, details, form):
    # type: (users.User, UserDetailsTO, SubmitDynamicFormRequestTO) -> FormSubmittedCallbackResultTO
    form_key = OcaForm.create_key(form.id, service_user)
    oca_form = form_key.get()  # type: OcaForm
    # Check if form is no longer accepting responses, else return error
    if oca_form.finished:  # TODO: replace with not oca_form.visible and not form.test
        user = create_app_user_by_email(details.email, details.app_id)
        lang = get_user_profile(user).language
        error = translate(lang, 'oca.form_ended_error')
        return FormSubmittedCallbackResultTO(valid=False, error=error)

    try_or_defer(_save_form_submission, details, form, service_user)
    return FormSubmittedCallbackResultTO()


def _save_form_submission(user_details, form_result, service_user):
    # type: (UserDetailsTO, SubmitDynamicFormRequestTO, users.User) -> None
    oca_form = OcaForm.create_key(form_result.id, service_user).get()  # type: OcaForm
    enabled_integrations = [i for i in oca_form.integrations if i.enabled]
    submission = FormSubmission(form_id=form_result.id,
                                user=user_details.toAppUser().email(),
                                version=form_result.version,
                                test=form_result.test,
                                pending_integration_submits=[i.provider for i in enabled_integrations])
    if submission.pending_integration_submits:
        # Sensitive info will be removed once it has been submitted to all integrations
        sections = form_result.sections
    else:
        with users.set_user(service_user):
            form = service_api.get_form(submission.form_id)
        sections = remove_sensitive_answers(form.sections, form_result.sections)
    submission.sections = [s.to_dict() for s in sections]
    submission.put()
    try_or_defer(update_form_statistics, service_user, submission, get_random_shard_number(submission.form_id))
    schedule_tasks([create_task(_submit_form_to_integration, service_user, i.provider, submission.key, form_result.id,
                                user_details)
                    for i in enabled_integrations])


def _submit_form_to_integration(service_user, integration_provider, submission_key, form_id, user_details):
    # type: (users.User, str, ndb.Key, long, UserDetailsTO) -> None
    integration_key = FormIntegrationConfiguration.create_key(service_user, integration_provider)
    oca_form_key = OcaForm.create_key(form_id, service_user)
    submission, config, oca_form = ndb.get_multi([submission_key, integration_key, oca_form_key])
    if not config or not config.enabled:
        if integration_provider != FormIntegrationProvider.EMAIL:
            logging.info('Integration %s not enabled', integration_provider)
            return
    form_integration = get_form_integration(integration_provider, config)
    filtered_integrations = [i for i in oca_form.integrations if i.provider == integration_provider]
    if not filtered_integrations:
        logging.warning('Not submitting form integration, provider %s not found.', integration_provider)
        return
    integration_model = filtered_integrations[0]  # type: FormIntegration
    if not integration_model.enabled:
        logging.info('Integration %s for form %d not enabled', integration_provider, form_id)
        return
    with users.set_user(service_user):
        form = service_api.get_form(form_id)
    service_profile = get_service_profile(oca_form.service_user)
    reference = form_integration.submit(integration_model.configuration, submission, form, service_profile,
                                        user_details)
    try_or_defer(_set_reference_and_remove_sensitive_info, form, submission_key, reference, integration_provider)


@ndb.transactional()
def _set_reference_and_remove_sensitive_info(form, submission_key, reference, integration_provider):
    # type: (DynamicFormTO, ndb.Key, unicode, unicode) -> None
    submission = submission_key.get()  # type: FormSubmission
    submission.pending_integration_submits = [s for s in submission.pending_integration_submits if
                                              s != integration_provider]
    if reference:
        submission.external_reference = reference
    # This was the last integration - remove sensitive data from the submission
    if not submission.pending_integration_submits:
        section_values = FormSectionValueTO.from_list(submission.sections)
        remove_sensitive_answers(form.sections, section_values)
        submission.sections = [s.to_dict() for s in section_values]
    submission.put()


def get_form_integrations(user):
    # type: (users.User) -> list[FormIntegration]
    return FormIntegrationConfiguration.list_by_user(user)


def update_form_integration(user, provider, data):
    key = FormIntegrationConfiguration.create_key(user, provider)
    integration = key.get() or FormIntegrationConfiguration(key=key)  # type: FormIntegrationConfiguration
    integration.enabled = data['enabled']
    integration.configuration = data['configuration']
    integration.put()
    # TODO: validate that the configuration is valid, throw error otherwise
    return integration
