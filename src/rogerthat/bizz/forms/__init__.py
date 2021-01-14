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

from google.appengine.ext import db, ndb
from google.appengine.ext.deferred import deferred
from typing import List

from mcfw.consts import MISSING
from mcfw.rpc import arguments, returns
from rogerthat.capi.forms import testForm, test_form_response_handler
from rogerthat.dal.mobile import get_mobile_key_by_account
from rogerthat.dal.profile import get_service_profile, get_profile_infos, get_user_profile
from rogerthat.dal.service import get_service_identity
from rogerthat.models import ServiceMenuDef, Message
from rogerthat.models.forms import Form, FormSubmissions, Submission
from rogerthat.rpc import users
from rogerthat.rpc.rpc import logError, CAPI_KEYWORD_PUSH_DATA
from rogerthat.rpc.service import logServiceError
from rogerthat.service.api import messaging
from rogerthat.service.api.forms.service_callbacks import form_submitted, form_submitted_response_handler
from rogerthat.to.forms import DynamicFormTO, ValidatedComponentTO, ParagraphComponentTO, FieldComponentTO, \
    VALIDATOR_MAPPING, FormSectionTO, SelectComponentTO, ValueTO, FormComponentType, SubmitDynamicFormRequestTO, \
    TestFormRequestTO, NextActionSectionTO, NextActionURLTO, NextActionTO
from rogerthat.to.messaging import MemberTO, AnswerTO
from rogerthat.to.push import TestFormNotification
from rogerthat.to.service import UserDetailsTO
from rogerthat.translations import localize
from .exceptions import FormValidationException, EmptyPropertyException, FormNotFoundException, \
    FormInUseException, LocalizedSubmitFormException, NoPermissionToFormException, SubmitFormException
from rogerthat.utils.service import create_service_identity_user


@returns(Form)
@arguments(form_id=(int, long), service_user=users.User)
def get_form(form_id, service_user=None):
    # type: (int, users.User) -> Form
    form = Form.create_key(form_id).get()
    if not form:
        raise FormNotFoundException(form_id)
    if service_user:
        if form.service != service_user.email():
            raise NoPermissionToFormException(form_id)
    return form


@returns([Form])
@arguments(service_user=users.User)
def list_forms(service_user):
    # type: (users.User) -> list[DynamicFormTO]
    return Form.list_by_service(service_user.email())


@returns(Form)
@arguments(service_user=users.User, form=DynamicFormTO)
def create_form(service_user, form):
    # type: (users.User, DynamicFormTO) -> Form
    model = Form(service=service_user.email())
    return _update_form(model, form)


@returns(Form)
@arguments(service_user=users.User, form=DynamicFormTO)
def update_form(service_user, form):
    # type: (users.User, DynamicFormTO) -> Form
    _validate_property(form, DynamicFormTO.id)
    model = get_form(form.id, service_user)
    updated_form = _update_form(model, form)
    deferred.defer(_update_smi_form_version, service_user, form.id)
    return updated_form


@arguments(service_user=users.User, form_id=(int, long))
def delete_form(service_user, form_id):
    # type: (users.User, int) -> None
    item = ServiceMenuDef.list_by_form(service_user, form_id).get()
    if item:
        raise FormInUseException(form_id, item.label)
    form = get_form(form_id, service_user)
    form.key.delete()
    deferred.defer(delete_form_submissions, service_user, form_id, False)


@arguments(service_user=users.User, form_id=(int, long), app_user=users.User)
def delete_form_submission(service_user, form_id, app_user):
    get_form(form_id, service_user)  # validate permission
    _del_submission(form_id, app_user)


@ndb.transactional()
def _del_submission(form_id, app_user):
    submissions = FormSubmissions.create_key(form_id, app_user).get()  # type: FormSubmissions
    if submissions:
        if submissions.submissions:
            submissions.submissions.pop(0)
        if submissions.submissions:
            submissions.put()
        else:
            submissions.key.delete()


@arguments(service_user=users.User, form_id=(int, long), validate=bool)
def delete_form_submissions(service_user, form_id, validate=True):
    if validate:
        get_form(form_id, service_user)
    ndb.delete_multi(FormSubmissions.list_by_form(form_id).fetch(keys_only=True))


@arguments(service_user=users.User, form_id=(int, long), testers=[users.User])
def test_form(service_user, form_id, testers):
    # type: (users.User, int, List[users.User]) -> None
    form = get_form(form_id, service_user)
    request = TestFormRequestTO(id=form_id, version=form.version)
    to_put = []
    prof = get_service_profile(service_user)
    branding = get_service_identity(create_service_identity_user(service_user)).menuBranding
    caption = localize(prof.defaultLanguage, 'forms.test_form')
    answers = [AnswerTO(id_=u'test',
                        caption=caption,
                        action=u'form://%d?version=%d&test=true' % (form_id, form.version))]
    flags = Message.FLAG_AUTO_LOCK
    alert_flags = Message.ALERT_FLAG_VIBRATE
    tag = None
    message = localize(prof.defaultLanguage, 'forms.click_button_to_test')
    for user_profile in get_profile_infos(testers):
        mobiles = db.get([get_mobile_key_by_account(mobile_detail.account) for mobile_detail in user_profile.get_mobiles().values()])
        has_other = False
        android_mobile = None
        for mobile in mobiles:
            if mobile.is_android:
                android_mobile = mobile
            else:
                has_other = True
        if has_other:
            messaging.send(None, None, message, answers, flags, [MemberTO.from_user(user_profile.user)], branding, tag,
                           alert_flags=alert_flags)
        else:
            title = localize(prof.defaultLanguage, 'forms.test_form_x', title=form.title)
            body = localize(prof.defaultLanguage, 'forms.click_to_test_your_form')
            kwargs = {CAPI_KEYWORD_PUSH_DATA: TestFormNotification(title, body, form.id, form.version)}
            to_put.extend(testForm(test_form_response_handler, logError, user_profile.user, request=request,
                                   MOBILE_ACCOUNT=android_mobile, DO_NOT_SAVE_RPCCALL_OBJECTS=True, **kwargs))
    db.put(to_put)


def _update_smi_form_version(service_user, form_id):
    db.run_in_transaction(__update_smi_form_version, service_user, form_id)


def __update_smi_form_version(service_user, form_id):
    from rogerthat.bizz.service import bump_menuGeneration_of_all_identities_and_update_friends
    form = get_form(form_id, service_user)
    menu_items = ServiceMenuDef.list_by_form(service_user, form.id)  # type: list[ServiceMenuDef]
    to_put = []
    for menu_item in menu_items:
        menu_item.form_version = form.version
        to_put.append(menu_item)
    if to_put:
        db.put(to_put)
        bump_menuGeneration_of_all_identities_and_update_friends(service_user)


def submit_form(request, app_user):
    # type: (SubmitDynamicFormRequestTO, users.User) -> None
    form = get_form(request.id)
    # Allow unlimited responses when testing
    if not request.test:
        submissions_key = FormSubmissions.create_key(form.id, app_user)
        submissions = submissions_key.get() or FormSubmissions(key=submissions_key,
                                                               form_id=form.id)
        if form.max_submissions > 0:
            submission_count = len(submissions.submissions)
            if submission_count >= form.max_submissions:
                raise LocalizedSubmitFormException('forms.max_submission_count_reached',
                                                   submission_count=submission_count)
        submissions.submissions.append(Submission())
        submissions.put()
    service_user = users.User(form.service)
    user_profile = get_user_profile(app_user)
    result = form_submitted(form_submitted_response_handler, logServiceError, get_service_profile(service_user),
                            user_details=[UserDetailsTO.fromUserProfile(user_profile)],
                            form=request, PERFORM_CALLBACK_SYNCHRONOUS=True)
    if not result.valid:
        raise SubmitFormException(result.error)


def _validate_form(form):
    # type: (DynamicFormTO) -> None
    _validate_property(form, DynamicFormTO.title)
    if form.max_submissions is not MISSING:
        if form.max_submissions == 0 or form.max_submissions < -1 or form.max_submissions > 1000:
            raise FormValidationException(
                'max_submissions must be -1 (unlimited submissions) or greater than 0 and less than 1000')
    if not form.sections:
        raise FormValidationException('A form should have at least one section')
    unique_ids = []
    for section in form.sections:
        if section.id in unique_ids:
            raise FormValidationException('Section ids must be unique, id %s is used by multiple sections' % section.id)
        unique_ids.append(section.id)
    for section in form.sections:
        _validate_section(section, unique_ids)

    if form.submission_section is not MISSING and form.submission_section:
        for component in form.submission_section.components:
            if component.type not in [FormComponentType.PARAGRAPH]:
                raise FormValidationException(
                    'Component of type "%s" is not allowed in the submission section' % component.type)
        _validate_section(form.submission_section, [], False)


def _validate_property(parent, prop):
    val = getattr(parent, prop.__name__, MISSING)
    if val is MISSING or not val:
        raise EmptyPropertyException(prop.__name__, parent)


def _validate_values(values, section_ids):
    # type: (list[ValueTO], list[unicode]) -> None
    for value in values:
        _validate_property(value, ValueTO.value)
        _validate_property(value, ValueTO.label)
        _validate_next_action(value.next_action, section_ids)


def _validate_next_action(value, section_ids):
    # type: (NextActionTO, list[str]) -> None
    if value is not MISSING and value:
        if isinstance(value, NextActionSectionTO):
            if value.section not in section_ids:
                raise FormValidationException(
                    'Section with id "%s" does not exist (in value %s)' % (value.section, value))
        if isinstance(value, NextActionURLTO):
            _validate_property(value, NextActionURLTO.url)


def _validate_section(section, section_ids, validate_id=True):
    # type: (FormSectionTO, list[unicode], bool) -> None
    if validate_id:
        _validate_property(section, FormSectionTO.id)
    unique_ids = []
    if section.branding in (None, MISSING) or (not section.branding.avatar_url and not section.branding.logo_url):
        section.branding = None
    _validate_next_action(section.next_action, section_ids)
    for component in section.components:
        if isinstance(component, FieldComponentTO):
            _validate_property(component, FieldComponentTO.id)
            if component.id in unique_ids:
                raise FormValidationException(
                    'Id "%s" is already used by another component in section "%s"' % (component.id, section.id))
            unique_ids.append(component.id)
        if isinstance(component, ParagraphComponentTO):
            # Title is mandatory for subtypes, but optional for paragraph
            if not type(component) == ParagraphComponentTO:
                _validate_property(component, ParagraphComponentTO.title)
            else:
                if (component.title is MISSING or not component.title) and (
                        component.description is MISSING or not component.description):
                    raise FormValidationException('A paragraph component should have at least a title or description')
        if isinstance(component, ValidatedComponentTO):
            unique_types = []
            allowed_validator_types = VALIDATOR_MAPPING.get(component.type, [])
            for validator in component.validators:
                if validator.type not in allowed_validator_types:
                    raise FormValidationException(
                        'Validator "%s" is not allowed for component of type "%s"' % (validator.type, component.type))
                if validator.type in unique_types:
                    raise FormValidationException(
                        'Duplicate validator "%s" in component with id "%s"' % (validator.type, component.id))
                else:
                    unique_types.append(validator.type)
        if isinstance(component, SelectComponentTO):
            _validate_property(component, SelectComponentTO.choices)
            _validate_values(component.choices, section_ids)


def _update_form(model, form):
    # type: (Form, DynamicFormTO) -> Form
    _validate_form(form)
    model.populate(
        title=form.title,
        sections=[s.to_dict() for s in form.sections],
        submission_section=form.submission_section and form.submission_section.to_dict(),
        max_submissions=form.max_submissions,
        version=model.version + 1,
    )
    model.put()
    return model


def delete_forms_by_service(service_user):
    ndb.delete_multi([form.key for form in Form.list_by_service(service_user.email())])
