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

from mcfw.consts import MISSING, REST_TYPE_TO
from mcfw.exceptions import HttpConflictException, HttpNotFoundException, HttpBadRequestException
from mcfw.restapi import rest, GenericRESTRequestHandler
from mcfw.rpc import returns, arguments
from rogerthat.bizz.app import create_app, get_app, AppDoesNotExistException, update_app, set_default_app, patch_app, \
    put_settings, get_news_settings, upload_news_backround_image, \
    save_firebase_settings_ios
from rogerthat.bizz.app_assets import get_app_assets, remove_app_asset, get_all_app_assets, get_app_asset, \
    remove_global_app_asset
from rogerthat.bizz.branding import save_core_branding
from rogerthat.bizz.default_brandings import remove_default_branding, get_default_brandings, \
    remove_default_global_branding, get_all_default_brandings, get_default_branding
from rogerthat.bizz.qrtemplate import get_app_qr_templates, store_app_qr_template, delete_app_qr_template, \
    create_default_qr_template_from_logo, QrTemplateRequiredException
from rogerthat.bizz.service import ServiceIdentityDoesNotExistException, InvalidAppIdException
from rogerthat.dal.app import get_apps, get_all_apps, get_app_settings
from rogerthat.exceptions.app import DuplicateAppIdException
from rogerthat.exceptions.branding import BrandingValidationException, BadBrandingZipException, \
    DefaultBrandingNotFoundExcpetion
from rogerthat.models import QRTemplate
from rogerthat.rpc.service import ServiceApiException
from rogerthat.to import FileTO, UploadInfoTO
from rogerthat.to.app import AppTO, AppQRTemplateTO, CreateAppTO, CreateAppQRTemplateTO, AppAssetFullTO, \
    DefaultBrandingTO, AppSettingsTO, NewsSettingsTO, NewsGroupTO
from rogerthat.to.branding import BrandingTO


@rest('/console-api/apps', 'post', type=REST_TYPE_TO)
@returns(AppTO)
@arguments(data=CreateAppTO)
def api_create_app(data):
    try:
        return AppTO.from_model(create_app(data))
    except DuplicateAppIdException as exception:
        raise HttpConflictException('duplicate_app_id', data={'app_id': exception.app_id})
    except InvalidAppIdException as exception:
        raise HttpBadRequestException('invalid_app_id', data={'app_id': exception.fields['app_id']})


@rest('/console-api/apps', 'get', silent_result=True)
@returns([AppTO])
@arguments(app_types=[int], visible=bool)
def api_list_apps(app_types=None, visible=True):
    if app_types:
        apps = get_apps(app_types, visible)
    else:
        apps = get_all_apps()
    return [AppTO.from_model(app) for app in apps]


@rest('/console-api/apps/<app_id:[^/]+>', 'get')
@returns(AppTO)
@arguments(app_id=unicode)
def api_get_app(app_id):
    try:
        return AppTO.from_model(get_app(app_id))
    except AppDoesNotExistException:
        raise HttpNotFoundException('app_not_found', data={'app_id': app_id})


@rest('/console-api/apps/<app_id:[^/]+>', 'put')
@returns(AppTO)
@arguments(app_id=unicode, data=AppTO)
def api_update_app(app_id, data):
    try:
        return AppTO.from_model(update_app(app_id, data))
    except AppDoesNotExistException:
        raise HttpNotFoundException('app_not_found', data={'app_id': app_id})
    except ServiceIdentityDoesNotExistException as e:
        raise HttpBadRequestException('service_identity_not_found', {'service_identity': e.fields['service_identity']})


@rest('/console-api/apps/<app_id:[^/]+>/partial', 'put')
@returns(dict)
@arguments(app_id=unicode, data=AppTO)
def api_patch_app(app_id, data):
    try:
        rogerthat_app, app = patch_app(app_id, data)
        return {
            'rogerthat_app': AppTO.from_model(rogerthat_app),
            'app': app,
        }
    except AppDoesNotExistException:
        raise HttpNotFoundException('app_not_found', data={'app_id': app_id})


@rest('/console-api/apps/<app_id:[^/]+>/qr-code-templates', 'get')
@returns([AppQRTemplateTO])
@arguments(app_id=unicode)
def api_get_qr_templates(app_id):
    try:
        templates = get_app_qr_templates(app_id)
        return [AppQRTemplateTO.from_model(tmpl, i == 0) for i, tmpl in enumerate(templates)] if templates else []
    except AppDoesNotExistException:
        raise HttpNotFoundException('app_not_found', data={'app_id': app_id})


@rest('/console-api/apps/<app_id:[^/]+>/qr-code-templates', 'post', type=REST_TYPE_TO)
@returns(AppQRTemplateTO)
@arguments(app_id=unicode, data=CreateAppQRTemplateTO)
def api_add_qr_template(app_id, data):
    """
    Args:
        app_id (unicode)
        data (CreateAppQRTemplateTO)
    """
    try:
        if not data.file or data.file is MISSING:
            raise HttpBadRequestException('missing_parameter', data={'parameter': 'file'})
        return AppQRTemplateTO.from_model(*store_app_qr_template(app_id, data))
    except AppDoesNotExistException:
        raise HttpNotFoundException('app_not_found', data={'app_id': app_id})
    except ServiceApiException as e:
        raise HttpBadRequestException('service_api_error', data=e.to_dict())


@rest('/console-api/apps/<app_id:[^/]+>/default-qr-code-template', 'post', type=REST_TYPE_TO)
@returns(AppQRTemplateTO)
@arguments(app_id=unicode, data=FileTO)
def api_create_default_qr_template(app_id, data):
    """
    Create a default qr template for an app using a logo.

    Args:
        app_id (unicode)
        data (FileTO): content of the logo
    """
    try:
        if not data.file or data.file is MISSING:
            raise HttpBadRequestException('missing_parameter', data={'parameter': 'file'})
        default_qr = create_default_qr_template_from_logo(app_id, data.file)
        if not default_qr:
            raise HttpConflictException('duplicate_default_qr_template')
        return AppQRTemplateTO.from_model(*default_qr)
    except AppDoesNotExistException:
        raise HttpNotFoundException('app_not_found', data={'app_id': app_id})
    except ServiceApiException as e:
        raise HttpBadRequestException('service_api_error', data=e.to_dict())


@rest('/console-api/apps/<app_id:[^/]+>/qr-code-templates/<key_name:[^/]+>', 'get')
@returns(AppQRTemplateTO)
@arguments(app_id=unicode, key_name=unicode)
def api_get_qr_template(app_id, key_name):
    try:
        template = QRTemplate.get_by_key_name(key_name)
        if not template:
            raise HttpNotFoundException('qr_template_not_found', data={'key_name': key_name})
        return AppQRTemplateTO.from_model(template)
    except AppDoesNotExistException:
        raise HttpNotFoundException('app_not_found', data={'app_id': app_id})


@rest('/console-api/apps/<app_id:[^/]+>/qr-code-templates/<key_name:[^/]+>', 'delete')
@returns()
@arguments(app_id=unicode, key_name=unicode)
def api_delete_qr_template(app_id, key_name):
    try:
        delete_app_qr_template(app_id, key_name)
    except AppDoesNotExistException:
        raise HttpNotFoundException('app_not_found', data={'app_id': app_id})
    except QrTemplateRequiredException:
        raise HttpConflictException('cannot_remove_qr_template')


@rest('/console-api/apps/<app_id:[^/]+>/core-branding', 'put', silent=True)
@returns(BrandingTO)
@arguments(app_id=unicode, data=FileTO)
def api_save_core_branding(app_id, data):
    try:
        return BrandingTO.from_model(save_core_branding(app_id, data.file))
    except AppDoesNotExistException:
        raise HttpNotFoundException('app_not_found', data={'app_id': app_id})
    except BadBrandingZipException as e:
        raise HttpBadRequestException('bad_branding_zip', data={'message': e.message})
    except BrandingValidationException as e:
        raise HttpBadRequestException('invalid_branding_error', data={'message': e.message})


@rest('/console-api/apps/<app_id:[^/]+>/assets', 'get')
@returns([AppAssetFullTO])
@arguments(app_id=unicode)
def api_get_app_assets(app_id):
    return [AppAssetFullTO.from_model(app_asset) for app_asset in get_app_assets(app_id)]


@rest('/console-api/apps/<app_id:[^/]+>/assets/<asset_type:[^/]+>', 'delete')
@returns(UploadInfoTO)
@arguments(app_id=unicode, asset_type=unicode)
def api_delete_app_asset(app_id, asset_type):
    remove_app_asset(app_id, asset_type)


@rest('/console-api/apps/<app_id:[^/]+>/default-brandings', 'get')
@returns([DefaultBrandingTO])
@arguments(app_id=unicode)
def api_get_default_brandings(app_id):
    return [DefaultBrandingTO.from_model(branding) for branding in get_default_brandings(app_id)]


@rest('/console-api/apps/<app_id:[^/]+>/default-brandings/<branding_type:[^/]+>', 'delete')
@returns()
@arguments(app_id=unicode, branding_type=unicode)
def api_delete_default_branding(app_id, branding_type):
    remove_default_branding(app_id, branding_type)


@rest('/console-api/apps/<app_id:[^/]+>/settings', 'get')
@returns(AppSettingsTO)
@arguments(app_id=unicode)
def api_get_app_settings(app_id):
    return AppSettingsTO.from_model(get_app_settings(app_id))


@rest('/console-api/apps/<app_id:[^/]+>/settings', 'put')
@returns(AppSettingsTO)
@arguments(app_id=unicode, data=AppSettingsTO)
def api_update_app_settings(app_id, data):
    return AppSettingsTO.from_model(put_settings(app_id, data))


@rest('/console-api/apps/<app_id:[^/]+>/settings/firebase-ios', 'put', silent=True)
@returns(AppSettingsTO)
@arguments(app_id=unicode, data=FileTO)
def api_save_firebase_settings(app_id, data):
    return AppSettingsTO.from_model(save_firebase_settings_ios(app_id, data.file))


@rest('/console-api/apps/<app_id:[^/]+>/news-settings', 'get')
@returns(NewsSettingsTO)
@arguments(app_id=unicode)
def api_get_news_settings(app_id):
    return get_news_settings(app_id)


@rest('/console-api/apps/<app_id:[^/]+>/news-settings/<group_id:[^/]+>/background-image', 'put')
@returns(NewsGroupTO)
@arguments(app_id=unicode, group_id=unicode)
def api_upload_news_background_image(app_id, group_id):
    request = GenericRESTRequestHandler.getCurrentRequest()
    uploaded_file = request.POST.get('file')
    return upload_news_backround_image(app_id, group_id, uploaded_file)

# Default/global settings - editor permissions are needed for these calls

@rest('/console-api/apps/<app_id:[^/]+>/set-default', 'post', type=REST_TYPE_TO)
@returns(AppTO)
@arguments(app_id=unicode, data=dict)
def api_set_default_app(app_id, data):
    try:
        return AppTO.from_model(set_default_app(app_id))
    except AppDoesNotExistException:
        raise HttpNotFoundException('app_not_found', data={'app_id': app_id})


@rest('/console-api/assets', 'get')
@returns([AppAssetFullTO])
@arguments()
def api_get_all_app_assets():
    return [AppAssetFullTO.from_model(asset) for asset in get_all_app_assets()]


@rest('/console-api/assets/<asset_id:[^/]+>', 'get')
@returns(AppAssetFullTO)
@arguments(asset_id=unicode)
def api_get_asset(asset_id):
    return AppAssetFullTO.from_model(get_app_asset(asset_id))


@rest('/console-api/assets/<asset_id:[^/]+>', 'delete')
@returns()
@arguments(asset_id=unicode)
def api_delete_global_app_asset(asset_id):
    try:
        remove_global_app_asset(asset_id)
    except ServiceApiException as exception:
        return HttpBadRequestException(exception.message)


@rest('/console-api/default-brandings', 'get')
@returns([DefaultBrandingTO])
@arguments()
def api_get_brandings():
    return [DefaultBrandingTO.from_model(branding) for branding in get_all_default_brandings()]


@rest('/console-api/default-brandings/<branding_id:[^/]+>', 'get')
@returns(DefaultBrandingTO)
@arguments(branding_id=unicode)
def api_get_default_branding_by_id(branding_id):
    try:
        return DefaultBrandingTO.from_model(get_default_branding(branding_id))
    except DefaultBrandingNotFoundExcpetion:
        raise HttpNotFoundException('default_branding_not_found', data={'branding_id': branding_id})


@rest('/console-api/default-brandings/<branding_id:[^/]+>', 'delete')
@returns()
@arguments(branding_id=unicode)
def api_delete_branding(branding_id):
    remove_default_global_branding(branding_id)


@rest('/console-api/default-brandings/<branding_id:[^/]+>', 'delete')
@returns()
@arguments(branding_id=unicode)
def api_delete_branding(branding_id):
    remove_default_global_branding(branding_id)
