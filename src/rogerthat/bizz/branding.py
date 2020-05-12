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

from HTMLParser import HTMLParser, HTMLParseError
import base64
from contextlib import closing
import hashlib
import json
import logging
import re
import time
from types import NoneType
import urllib
from zipfile import ZipFile, BadZipfile, ZIP_DEFLATED

import cloudstorage

from google.appengine.api import urlfetch
from google.appengine.ext import db, blobstore
from google.appengine.ext.deferred import deferred
from mcfw.properties import azzert
from mcfw.rpc import arguments, returns
from rogerthat.bizz.app import get_app
from rogerthat.bizz.i18n import update_translation_of_type
from rogerthat.bizz.job.update_friends import schedule_update_all_friends_of_service_user
from rogerthat.bizz.service.mfd import render_js_for_message_flow_designs
from rogerthat.consts import DEBUG, MAX_BRANDING_SIZE, MAX_APP_SIZE, MAX_BRANDING_PDF_SIZE, MAX_CORDOVA_SIZE
from rogerthat.dal import parent_key, put_and_invalidate_cache, put_in_chunks
from rogerthat.dal.mfd import get_service_message_flow_designs
from rogerthat.dal.profile import get_service_profile
from rogerthat.dal.service import get_service_identities, get_service_menu_items, get_service_identities_query
from rogerthat.exceptions.branding import BrandingValidationException, BrandingAlreadyExistsException, \
    BrandingInUseException, BadBrandingZipException
from rogerthat.models import Branding, PokeTagMap, ServiceTranslation, ServiceMenuDef, MessageFlowDesign, \
    ServiceIdentity
from rogerthat.models.utils import copy_model_properties
from rogerthat.rpc import users
from rogerthat.rpc.models import ServiceAPICallback
from rogerthat.rpc.rpc import mapping
from rogerthat.rpc.service import logServiceError
from rogerthat.service.api import system
from rogerthat.settings import get_server_settings
from rogerthat.to.branding import UpdatedBrandingTO
from rogerthat.utils import now, parse_color
from rogerthat.utils.languages import get_iso_lang
from rogerthat.utils.transactions import run_in_transaction
from rogerthat.utils.zip_utils import replace_file_in_zip


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

OLD_SYSTEM_BRANDING_HASHES = (u"3DD90F4045C190026B27B5BBFDA92A8176CD786A5BA597996516CB0744CF6662",
                              u"2AA36C31AF64986010E04EFD8CD8F035C141F55E17F26EE282CCC598EBE0E955",
                              u"75865721A260C1965CE0B1906D1E4B0E02E397FFD39B2770E540DF766E75A982",
                              u"FBC72AC5DBE2E5B7670947054703B40AAC6C7C14165E18641A70A83C2AE3D533",
                              u"357993B5B3153593A1C0148A611301F488CC7C33BA4DC7694171C6CD389F6EA8",
                              u"D8A57D5E8DB495F84DC3EC89C748E61D840F58BE0111469E678C539CBDA74F91",
                              u"DBFCBA9205C7BBB2C886B8098BF7BA3580F4E3126E0BD9528E107B39ABF72D5D",
                              u"616421CD786819EE2FB6BD8A6577D717FC7D3A5C1CE776BC58E57E4B3556F9A5",
                              u"54711E3FCAA41411B5DF02017EA029CB468241BD55610E838866DD0E020C9FAF",
                              u"CB8549E735E05FCD74F5B7C26190DBB6B5CEEBF1D13DC0C12B570C76697843DC",
                              u"CB7E7DA8DB6D919CD437C904EA5417C62012D6ECF88B629E5B71B7876BC30170",
                              u"507F495E4D02F4CA71A98ABDD628051E389B87B326974A3E450006A0D1928A4C")

NUNTIUZ_POKE_TAG = "nuntiuz_poke_tag://"
NUNTIUZ_POKE = "poke://"
ROGERTHAT_META_INFO_FILE = ".rogerthat-meta-info.txt"

TRANSLATIONS_JS_FILE = "__translations__.js"

BRANDING_BUCKET = '/rogerthat-brandings'


@returns(bool)
@arguments(content=str, branding_type=(int, long))
def is_branding(content, branding_type):
    try:
        _validate_branding_size(content, branding_type)
    except Exception, e:
        logging.debug(str(e), exc_info=1)
        return False

    stream = StringIO(content)
    try:
        zip_ = ZipFile(stream)
        try:
            _parse_and_validate_branding_zip(zip_)
        finally:
            zip_.close()
        return True
    except:
        logging.debug("Failure while parsing branding", exc_info=1)
        return False


def add_translations_to_all_app_brandings(service_user, branding_type, branding_translations_dict):
    # branding_translations_dict: { en_text : { web_lang : translation } }
    for translations in branding_translations_dict.itervalues():
        for web_lang in translations.keys():
            iso_lang = get_iso_lang(web_lang)
            translations[iso_lang] = translations.pop(web_lang)

    new_translations_content = _get_translations_js_content(service_user, branding_translations_dict)
    replaced_brandings = dict()  # { old_branding_hash : new_branding_hash }
    to_put = list()
    smis = list()

    for old_branding in Branding.list_by_type(service_user, branding_type):
        if old_branding.timestamp < 0:
            continue
        with closing(get_branding_blob_stream(old_branding)) as stream:
            with ZipFile(stream) as zip_file:
                try:
                    old_translations_content = zip_file.read(TRANSLATIONS_JS_FILE)
                except KeyError:
                    continue  # __translations__.js not found ==> it did not contain <x-rogerthat-t> tags

                if new_translations_content != old_translations_content:
                    zip_content = replace_file_in_zip(zip_file, TRANSLATIONS_JS_FILE, new_translations_content)
                    new_branding_hash = calculate_branding_hash(branding_type, zip_content)
                    kwargs = copy_model_properties(old_branding)
                    kwargs['blob'] = db.Blob(zip_content)
                    kwargs['timestamp'] = now()
                    to_put.append(Branding(key_name=new_branding_hash, **kwargs))

                    old_branding.timestamp *= -1
                    to_put.append(old_branding)

                    replaced_brandings[old_branding.hash] = new_branding_hash

                    for smi in get_service_menu_items_by_screen_branding(service_user, old_branding.hash):
                        smi.screenBranding = new_branding_hash
                        to_put.append(smi)
                        smis.append(smi)

    if to_put:
        logging.info('Updating %s models', len(to_put))
        put_and_invalidate_cache(*to_put)
        if smis:
            schedule_update_all_friends_of_service_user(service_user, bump_service_version=True)

        system.brandings_updated(brandings_updated_response_handler, logServiceError, get_service_profile(service_user),
                                 brandings=UpdatedBrandingTO.from_dict(replaced_brandings),
                                 reason=UpdatedBrandingTO.REASON_NEW_TRANSLATIONS)


@mapping('system.brandings_updated.response_handler')
@returns()
@arguments(context=ServiceAPICallback, result=NoneType)
def brandings_updated_response_handler(context, result):
    pass


def _store_branding_translations(service_user, translation_strings):
    return update_translation_of_type(service_user, ServiceTranslation.BRANDING_CONTENT,
                                      translation_strings)


def _get_translations_js_content(service_user, branding_translations_dict):
    rt_translations = dict(defaultLanguage=get_service_profile(service_user).defaultLanguage,
                           values=branding_translations_dict)
    return '''
/**
 * Auto-generated file. DO NOT MODIFY.
 */

var rogerthat_translations = %s;
if (typeof rogerthat !== "undefined") {
    rogerthat.util._translations = rogerthat_translations;
}
''' % json.dumps(rt_translations)


def _create_new_zip(service_user, branding_type, zip_, html, skip_meta_file=False):
    new_zip_stream = StringIO()
    new_zip_ = ZipFile(new_zip_stream, 'w', compression=ZIP_DEFLATED)
    translation_strings = set()
    translation_strings_parser = HtmlTranslationStringsExtractorParser(translation_strings.add)
    for file_name in set(zip_.namelist()):
        if branding_type == Branding.TYPE_NORMAL and file_name == 'branding.html':
            new_zip_.writestr(file_name, html)
        elif branding_type == Branding.TYPE_APP and file_name == 'app.html' or \
                branding_type == Branding.TYPE_CORDOVA and file_name == 'cordova.html':
            translation_strings_parser.feed(html)
            new_zip_.writestr("branding.html", html)
        else:
            contents = zip_.read(file_name)
            if file_name.endswith('.htm') or file_name.endswith('.html'):
                translation_strings_parser.feed(contents)
            new_zip_.writestr(file_name, contents)

    if branding_type in (Branding.TYPE_APP, Branding.TYPE_CORDOVA,) and translation_strings:
        branding_translations_dict, updated = _store_branding_translations(service_user, translation_strings)

        if branding_translations_dict or updated:
            logging.debug('Adding %s to branding.\n\nrogerthat.js found in script tag: %s\n%s found in script tag: %s',
                          TRANSLATIONS_JS_FILE,
                          translation_strings_parser.js_rogerthat_script_found,
                          TRANSLATIONS_JS_FILE,
                          translation_strings_parser.js_translations_script_found)

            translations_js_content = _get_translations_js_content(service_user, branding_translations_dict)
            logging.debug('%s\n\n%s', TRANSLATIONS_JS_FILE, translations_js_content)
            new_zip_.writestr(TRANSLATIONS_JS_FILE, translations_js_content)

            if branding_type in (
                Branding.TYPE_CORDOVA,) and not translation_strings_parser.js_translations_script_found or \
                    translation_strings_parser.js_rogerthat_script_found and not translation_strings_parser.js_translations_script_found:
                logging.debug('Adding script tag for %s', TRANSLATIONS_JS_FILE)
                m = re.search('</\\s*head>', html, re.I) or re.search('</\\s*body>', html, re.I)
                html = html.replace(m.group(), '<script src="%s"></script>\n%s' % (TRANSLATIONS_JS_FILE, m.group()))
                new_zip_.writestr('branding.html', html)

    if service_user and not skip_meta_file:
        admin_user = service_user  # XXX: admin user should be argument of the function
        _add_meta_data(new_zip_, admin_user)
    new_zip_.close()
    zip_content = new_zip_stream.getvalue()
    return zip_content


def get_branding_cloudstorage_path(branding_hash, service_user):
    if service_user:
        folder_name = service_user.email()
    else:
        folder_name = '_none'
    return "%s/%s/%s.zip" % (BRANDING_BUCKET, folder_name, branding_hash)


def _create_branding(hash_, zip_content, description, service_user, branding_type, meta_properties, pokes):
    if pokes and not service_user:
        raise BrandingValidationException('Cannot create branding with one or more poke tags without a service user')

    filename = get_branding_cloudstorage_path(hash_, service_user)
    with cloudstorage.open(filename, 'w') as f:
        f.write(zip_content)

    blobstore_filename = '/gs' + filename
    blobstore_key = blobstore.create_gs_key(blobstore_filename)

    b = Branding(key_name=hash_)
    b.blob_key = blobstore_key.decode('utf-8')
    b.description = description
    b.timestamp = now()
    b.user = service_user
    b.pokes = list()
    b.type = branding_type
    color_scheme = meta_properties.get('color-scheme') or Branding.DEFAULT_COLOR_SCHEME
    b.menu_item_color = meta_properties.get('menu-item-color') or Branding.DEFAULT_MENU_ITEM_COLORS[color_scheme]
    b.content_type = meta_properties.get('content-type') or Branding.CONTENT_TYPE_HTML
    b.orientation = meta_properties.get('orientation') or Branding.DEFAULT_ORIENTATION
    puts = [b]
    for poke_hash, unicode_tag in pokes:
        ptm = PokeTagMap(key_name=poke_hash, parent=parent_key(service_user))
        ptm.tag = unicode_tag
        b.pokes.append(ptm.key())
        puts.append(ptm)

    db.put(puts)
    return b


def get_branding_blob_stream(branding):
    """A utility function to return a stream for the branding blob,
       mostly used with ZipFile

    Args:
        branding (Branding)

    Returns:
        a file-like object or None
    """

    if not branding:
        return

    stream = None
    if branding.blob_key:
        if DEBUG:
            blob_info = blobstore.get(branding.blob_key)
            if blob_info:
                stream = blob_info.open()
        else:
            filename = get_branding_cloudstorage_path(branding.hash, branding.user)
            try:
                stream = cloudstorage.open(filename, 'r')
            except cloudstorage.errors.NotFoundError:
                pass
    else:
        stream = StringIO(branding.blob)

    return stream


@returns(NoneType)
@arguments(zip_content=str, branding_type=(int, long))
def _validate_branding_size(zip_content, branding_type=Branding.TYPE_NORMAL):
    if branding_type == Branding.TYPE_NORMAL and len(zip_content) > MAX_BRANDING_SIZE:
        logging.debug("Size of branding zip exceeds maximum size (%s bytes) with (%s bytes)" % (
            MAX_BRANDING_SIZE, len(zip_content)))
        raise BrandingValidationException("Size of branding zip exceeds maximum size (%s bytes)" % (MAX_BRANDING_SIZE))
    if branding_type == Branding.TYPE_APP and len(zip_content) > MAX_APP_SIZE:
        logging.debug(
            "Size of app zip exceeds maximum size (%s bytes) with (%s bytes)" % (MAX_APP_SIZE, len(zip_content)))
        raise BrandingValidationException("Size of app zip exceeds maximum size (%s bytes)" % (MAX_APP_SIZE))
    if branding_type == Branding.TYPE_CORDOVA and len(zip_content) > MAX_CORDOVA_SIZE:
        logging.debug(
            "Size of cordova zip exceeds maximum size (%s bytes) with (%s bytes)" % (
                MAX_CORDOVA_SIZE, len(zip_content)))
        raise BrandingValidationException("Size of cordova zip exceeds maximum size (%s bytes)" % (MAX_CORDOVA_SIZE))


@returns(Branding)
@arguments(service_user=users.User, zip_stream=type(StringIO()), description=unicode)
def store_branding(service_user, zip_stream, description):
    azzert(get_service_profile(service_user) is not None)

    zip_stream.seek(0)

    try:
        zip_ = ZipFile(zip_stream)
    except BadZipfile as e:
        raise BadBrandingZipException(e.message)

    return store_branding_zip(service_user, zip_, description)


@returns(Branding)
@arguments(service_user=users.User, pdf_stream=type(StringIO()), description=unicode)
def store_branding_pdf(service_user, pdf_stream, description):
    from PyPDF2.pdf import PdfFileReader
    pdf_stream.seek(0)
    # Test if the file is a valid PDF
    try:
        error_stream = StringIO()  # Get rid of the zero-index warnings
        doc = PdfFileReader(pdf_stream, strict=False, warndest=error_stream)
        logging.info("Uploaded pdf contains %s pages", doc.numPages)
        del doc
    except:
        logging.warning("Failed to validate branding PDF", exc_info=True)
        raise BrandingValidationException("The uploaded file could not be validated as a PDF file.")
    # Test if the file is not to large
    pdf_stream.seek(0)
    pdf_bytes = pdf_stream.read()
    if len(pdf_bytes) > MAX_BRANDING_PDF_SIZE:
        raise BrandingValidationException("Pdf Brandings should be smaller than %skB." % (MAX_BRANDING_PDF_SIZE / 1024))
    # Create branding file
    zip_stream = StringIO()

    with ZipFile(zip_stream, 'w') as bzf:
        bzf.writestr("branding.html", (u"""<!DOCTYPE html>
<!-- Created on %s -->
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <meta property="rt:style:content-type" content="%s"/>
    <script src="jquery/jquery-1.11.0.min.js"></script>
    <script src="rogerthat/rogerthat-1.0.js" type="text/javascript"></script>
</head>
<body>
<script>
    rogerthat.callbacks.ready(function(){
        if(rogerthat.system.os=="ios")
            window.location='embed.pdf';
        else if(rogerthat.system.os=="android"){
            var u=document.URL.split("/");
            var v="%s/branding/"+u[u.length-2]+"/embed.pdf";
            window.location='https://docs.google.com/viewer?url='+encodeURIComponent(v);
        }
    });
</script>
</body>
</html>""" % (now(), Branding.CONTENT_TYPE_PDF,
              get_server_settings().baseUrl)).encode('utf-8'))
        bzf.writestr("embed.pdf", pdf_bytes)
    zip_stream.seek(0)
    zip_content = zip_stream.getvalue()
    hash_ = calculate_branding_hash(Branding.TYPE_APP, zip_content)
    meta_properties = dict()
    meta_properties["content-type"] = Branding.CONTENT_TYPE_PDF
    return _create_branding(hash_, zip_content, description, service_user, Branding.TYPE_APP, meta_properties, list())


def calculate_branding_hash(branding_type, zip_content):
    hash_ = hashlib.sha256(zip_content).hexdigest().upper()
    if branding_type in (Branding.TYPE_CORDOVA,):
        return "cordova-%s" % hash_
    return hash_


@returns(Branding)
@arguments(service_user=users.User, zip_=ZipFile, description=unicode, skip_meta_file=bool)
def store_branding_zip(service_user, zip_, description, skip_meta_file=False):
    # type: (users.User, ZipFile, unicode) -> Branding
    try:
        pokes, html, branding_type, meta_properties = _parse_and_validate_branding_zip(zip_)

        # Remove previously added dimensions:
        html = re.sub("<meta\\s+property=\\\"rt:dimensions\\\"\\s+content=\\\"\\[\\d+,\\d+,\\d+,\\d+\\]\\\"\\s*/>", "",
                      html)

        try:
            zip_content = _create_new_zip(service_user, branding_type, zip_, html, skip_meta_file)
        except BadZipfile, e:
            raise BadBrandingZipException(reason=e.message)

        _validate_branding_size(zip_content, branding_type)

        hash_ = calculate_branding_hash(branding_type, zip_content)
        b = Branding.get_by_key_name(hash_)
        if b and b.user != service_user:
            raise BrandingAlreadyExistsException()

        def trans():
            return _create_branding(hash_, zip_content, description, service_user, branding_type, meta_properties,
                                    pokes)

        branding = run_in_transaction(trans, True)

        #
        # Try to add dimension information
        #

        if "</head>" in html:
            settings = get_server_settings()
            if not settings.brandingRendererUrl or branding_type in (Branding.TYPE_APP, Branding.TYPE_CORDOVA,):
                return branding

            if meta_properties.get('display-type', Branding.DISPLAY_TYPE_WEBVIEW) == Branding.DISPLAY_TYPE_NATIVE:
                return branding

            try:
                url = "%s?%s" % (settings.brandingRendererUrl, urllib.urlencode(
                    (('url', get_server_settings().baseUrl + '/branding/' + hash_ + '/branding.html?xrender=true'),)))
                response = urlfetch.fetch(url, deadline=10)
                if response.status_code != 200:
                    logging.error("Could not render branding to get dimensions.\n%s" % response.content)
                    return branding
            except:
                logging.warn("Failed to render dimensions")
                return branding

            html = html.replace("</head>",
                                '<meta property="rt:dimensions" content="' + response.content + '" /></head>')
        else:
            return branding

        zip_content = _create_new_zip(service_user, branding_type, zip_, html)
    finally:
        zip_.close()

    hash_ = calculate_branding_hash(branding_type, zip_content)
    b = Branding.get_by_key_name(hash_)
    if b and b.user != service_user:
        raise BrandingAlreadyExistsException()

    def trans2():
        branding.delete()
        return _create_branding(hash_, zip_content, description, service_user, branding_type, meta_properties, pokes)

    return run_in_transaction(trans2, True)


# Checks if the newly uploaded branding's meta file is the same as the newest branding with the same name's meta file.
# If it is the same and only_replace_if_newer is True, no hashes will be returned
# As a result replace_branding will not do anything if that's the case.
def get_brandings_to_replace(service_user, description, zip_, only_replace_if_newer):
    brandings = sorted(Branding.list_by_description(service_user, description), key=lambda b: b.timestamp)
    has_branding = len(brandings) > 0
    branding_hashes = [b.hash for b in brandings]
    if not only_replace_if_newer or not brandings:
        return branding_hashes, has_branding
    meta_content = zip_.read(ROGERTHAT_META_INFO_FILE)
    zip_stream = get_branding_blob_stream(brandings[-1])
    with closing(zip_stream):
        old_zip = ZipFile(zip_stream)
        if old_zip.read(ROGERTHAT_META_INFO_FILE) == meta_content:
            return [], has_branding
        else:
            return branding_hashes, has_branding


@returns(tuple)
@arguments(service_user=users.User, zip_stream=type(StringIO()), description=unicode, skip_meta_file=bool,
           only_replace_if_newer=bool)
def replace_branding(service_user, zip_stream, description, skip_meta_file=False, only_replace_if_newer=False):
    """
    Replaces existing brandings with the same description with the new branding.
    Updates every model that uses the updated brandings.
    Args:
        service_user (users.User)
        zip_stream(StringIO)
        description(unicode)
        skip_meta_file(bool)
        only_replace_if_newer(bool)
    Returns:
        tuple(Branding, list[Branding])
    """
    try:
        zip_ = ZipFile(zip_stream)
    except BadZipfile as e:
        raise BadBrandingZipException(e.message)
    original_branding_hashes, has_branding_with_description = get_brandings_to_replace(service_user, description, zip_,
                                                                                       only_replace_if_newer)
    if has_branding_with_description and not original_branding_hashes and only_replace_if_newer:
        logging.info('Branding %s is the same as previously uploaded branding with same description, not doing anything',
                     description)
        return None, None

    message_flows = MessageFlowDesign.list_by_service_user(service_user).fetch(None)  # type: list[MessageFlowDesign]
    service_identities = get_service_identities_query(service_user).fetch(None)
    menu_items = filter(lambda item: item.screenBranding in original_branding_hashes,
                        ServiceMenuDef.list_by_service(service_user))  # type: list[ServiceMenuDef]

    logging.info('Will replace %s brandings with new branding', len(original_branding_hashes))

    def trans():
        new_branding = store_branding_zip(service_user, zip_, description, skip_meta_file)

        if original_branding_hashes:
            # Mark brandings with same description as deleted
            deferred.defer(_mark_brandings_deleted, original_branding_hashes, _transactional=True)
            # Replace branding hash in menu items
            for menu_item in menu_items:
                menu_item.screenBranding = new_branding.hash
            to_put = menu_items

            # Replace branding hash in message flows
            branding_hash_re = re.compile('|'.join(original_branding_hashes))
            for flow in message_flows:
                must_update = False
                if flow.definition:
                    updated_flow_def = branding_hash_re.sub(new_branding.hash, flow.definition)
                    if flow.definition != updated_flow_def:
                        flow.definition = updated_flow_def
                        must_update = True
                if flow.xml:
                    updated_xml = branding_hash_re.sub(new_branding.hash, flow.xml)
                    if flow.xml != updated_xml:
                        flow.xml = updated_xml
                        # update flow definitions
                        render_js_for_message_flow_designs([flow], False)
                        must_update = True
                else:
                    logging.debug('Not updating flow %s xml because its xml is %s', flow.name, flow.xml)
                if must_update:
                    to_put.append(flow)

            # Replace branding hash in service identities
            for service_identity in service_identities:  # type: ServiceIdentity
                assert isinstance(service_identity, ServiceIdentity)
                if service_identity.contentBrandingHash in original_branding_hashes:
                    service_identity.contentBrandingHash = new_branding.hash
                if service_identity.descriptionBranding in original_branding_hashes:
                    service_identity.descriptionBranding = new_branding.hash
                if service_identity.menuBranding in original_branding_hashes:
                    service_identity.menuBranding = new_branding.hash
                if service_identity.homeBrandingHash in original_branding_hashes:
                    service_identity.homeBrandingHash = new_branding.hash
                to_put.append(service_identity)

            put_and_invalidate_cache(*to_put)
            schedule_update_all_friends_of_service_user(get_service_profile(service_user), bump_service_version=True)

        return new_branding, original_branding_hashes

    return run_in_transaction(trans, xg=True)


def _mark_brandings_deleted(branding_hashes):
    to_put = []
    for branding in Branding.get_by_key_name(branding_hashes):
        if branding.timestamp > 0:
            branding.timestamp = 0 - branding.timestamp
            to_put.append(branding)
    put_in_chunks(to_put)


@returns([ServiceMenuDef])
@arguments(service_user=users.User, branding_key=unicode)
def get_service_menu_items_by_screen_branding(service_user, branding_key):
    return (smi for smi in get_service_menu_items(service_user)
            if smi.screenBranding and smi.screenBranding == branding_key)


@returns(NoneType)
@arguments(service_user=users.User, key=unicode)
def delete_branding(service_user, key):
    branding = Branding.get_by_key_name(key)
    if branding:
        azzert(branding.user == service_user)
        message_flow_designs = get_service_message_flow_designs(service_user)
        service_identities = get_service_identities(service_user)
        menu_items_with_branding = get_service_menu_items_by_screen_branding(service_user, key)
        service_profile = get_service_profile(service_user)
        validate_delete_branding(
            key, message_flow_designs, service_identities, menu_items_with_branding, service_profile)
        branding.timestamp = 0 - branding.timestamp
        branding.put()


def validate_delete_branding(key, message_flow_flow_designs, service_identities, menu_items_with_branding,
                             service_profile):
    for mfd in message_flow_flow_designs:
        if not mfd.deleted and mfd.xml and key in mfd.xml:
            raise BrandingInUseException(
                u"Branding is used in message flow '%s' and thus can't be deleted!" % mfd.name, id=key,
                type='message_flow_design', identifier=mfd.name)

    for service_identity in service_identities:
        if service_identity.descriptionBranding and service_identity.descriptionBranding == key:
            raise BrandingInUseException(u"Cannot delete the branding that is used for your profile description!",
                                         id=key, type='description_branding', identifier=service_identity)
        if service_identity.menuBranding and service_identity.menuBranding == key:
            raise BrandingInUseException(u"Cannot delete the branding %s that is used for your menu!", id=key,
                                         type='menu_branding')
        if service_identity.homeBrandingHash and service_identity.homeBrandingHash == key:
            raise BrandingInUseException(u"Cannot delete a branding that is used for your homescreen!", id=key,
                                         type='home_branding')
    for smi in menu_items_with_branding:
        raise BrandingInUseException(u"Branding is used in menu item '%s' and thus can't be deleted!" % smi.label,
                                     id=key, type='menu_item', identifier=smi.label)

    if service_profile.broadcastBranding == key:
        raise BrandingInUseException(u"Branding is used for broadcast settings and thus can't be deleted!", id=key,
                                     type='broadcast_branding')


class HtmlTranslationStringsExtractorParser(HTMLParser):

    def __init__(self, translationFoundCallback):
        HTMLParser.__init__(self)
        self.translationFoundCallback = translationFoundCallback
        self.recording = False
        self.js_translations_script_found = False
        self.js_rogerthat_script_found = False
        self._js_rogerthat_script_regex = re.compile('rogerthat/rogerthat-(\d+\.)+js')

    def handle_starttag(self, tag, attrs):
        lower_tag = tag.lower()
        if self.recording:
            self.recording = False
            return
        if lower_tag == "x-rogerthat-t":
            self.recording = True
        elif lower_tag == "script":
            for attr, val in attrs:
                if attr.lower() == 'src':
                    if val == '__translations__.js':
                        self.js_translations_script_found = True
                        break
                    elif not self.js_rogerthat_script_found and self._js_rogerthat_script_regex.match(val):
                        self.js_rogerthat_script_found = True
                        break

    def handle_endtag(self, tag):
        if self.recording:
            self.recording = False

    def handle_startendtag(self, tag, attrs):
        if self.recording:
            self.recording = False

    def handle_data(self, data):
        if self.recording:
            self.translationFoundCallback(data)


class BrandingHtmlValidationParser(object, HTMLParser):

    def __init__(self, javascript_allowed, urls_allowed, files):
        HTMLParser.__init__(self)
        self.hasCharsetProperty = False
        self._in_head_section = False
        self.prohibited_tags = ['applet', 'object', 'embed']
        if not javascript_allowed:
            self.prohibited_tags.append('script')
        self.pokes = set()
        self.urls_allowed = urls_allowed
        self.meta_properties = dict()
        self.files = files

    def handle_starttag(self, tag, attrs):
        lower_tag = tag.lower()
        if lower_tag in self.prohibited_tags:
            raise BrandingValidationException("%s is a prohibited html tag." % tag)
        if lower_tag == 'head':
            self._in_head_section = True
        elif self._in_head_section and lower_tag == 'meta' and not self.hasCharsetProperty:
            attr_found = False
            for attr, val in attrs:
                if attr.lower() == 'charset' and 'utf-8' in val.strip().lower():
                    self.hasCharsetProperty = True
                    break
                if attr.lower() == 'http-equiv' and val.strip().lower() == 'content-type':
                    attr_found = True
                    break
            if attr_found:
                for attr, val in attrs:
                    if attr.lower() == 'content' and val.strip().lower().replace(' ', '') == 'text/html;charset=utf-8':
                        self.hasCharsetProperty = True
                        break
        for name, value in attrs:
            if lower_tag == "a" and name == "href" and value and value.startswith(NUNTIUZ_POKE_TAG):
                tag = value[len(NUNTIUZ_POKE_TAG):]
                self.pokes.add(tag.decode('utf-8'))
            elif lower_tag == "meta" and name == "property" and value.startswith("rt:style:"):
                rt_style = value[9:]  # strip off "rt:style:"
                content_attrs = [v for n, v in attrs if n == "content"]
                if content_attrs:
                    content = content_attrs[0]
                    self.meta_properties[rt_style] = content
                    if rt_style == "color-scheme":
                        if content not in Branding.COLOR_SCHEMES:
                            raise BrandingValidationException(u"Invalid color scheme: %s" % content)
                    elif rt_style.endswith('-color'):
                        color = content[1:] if content.startswith('#') else content
                        try:
                            parse_color(color)
                        except:
                            raise BrandingValidationException(u"Invalid color in %s: %s" % (value, content))
                        else:
                            self.meta_properties[rt_style] = color
                    elif rt_style == "orientation":
                        if content not in Branding.ORIENTATIONS:
                            raise BrandingValidationException(u"Invalid orientation: %s" % content)
                    elif rt_style == 'display-type':
                        if content not in Branding.DISPLAY_TYPES:
                            raise BrandingValidationException(
                                u'Invalid display type: %s. Allowed display types are %s.' % (
                                    content, u', '.join(Branding.DISPLAY_TYPES)
                                ))
                        if u'logo.jpg' not in self.files:
                            raise BrandingValidationException(u'Missing file logo.jpg for display type %s' % content)

            elif value is not None:
                if ".." in value or '%2e%2e' in value:
                    if not value.startswith('http://') and not value.startswith('https://'):
                        raise BrandingValidationException("dotdot (..) sequence is not allowed in html attributes.")
                if not self.urls_allowed and "://" in value:
                    raise BrandingValidationException("External links or objects are not allowed.")

    def handle_endtag(self, tag):
        if self._in_head_section and tag.lower() == 'meta':
            self._in_head_section = False


def _parse_and_validate_html(html, filename, js_allowed, urls_allowed, files):
    logging.info("Validating %s:\n%s" % (filename, html.decode('utf8')))
    parser = BrandingHtmlValidationParser(js_allowed, urls_allowed, files)
    try:
        parser.feed(html)
    except HTMLParseError as e:
        raise BrandingValidationException(e.msg)
    if not parser.hasCharsetProperty:
        raise BrandingValidationException(
            "The HTML file <b>%s</b> does not contain the charset encoding <b>&lt;meta charset=\"UTF-8\"&gt;</b> in the head section." % filename)
    pokes = set()
    for unicode_tag in parser.pokes:
        str_tag = unicode_tag.encode('utf-8')
        hash_ = hashlib.sha256(str_tag).hexdigest()
        html = html.replace("%s%s" % (NUNTIUZ_POKE_TAG, str_tag), "%s%s" % (NUNTIUZ_POKE, hash_))
        pokes.add((hash_, unicode_tag))
    return html, pokes, parser.meta_properties


def _parse_and_validate_branding_zip(zip_):
    files = [fi.filename for fi in zip_.filelist]
    logging.debug('Files in branding: %s', files)
    if ".hacked" in files:
        raise BrandingValidationException("zip file may not contain a .hacked file in the root directory.")
    if "branding.html" in files:
        branding_type = Branding.TYPE_NORMAL
        html_file = "branding.html"
    elif "app.html" in files:
        branding_type = Branding.TYPE_APP
        html_file = "app.html"
    elif "cordova.html" in files:
        branding_type = Branding.TYPE_CORDOVA
        html_file = "cordova.html"
    else:
        raise BrandingValidationException(
            "zip file does not contain a branding.html, app.html or cordova.html file in the root directory.")

    scripts_allowed = branding_type in (Branding.TYPE_APP, Branding.TYPE_CORDOVA,)
    html, pokes, meta_properties = _parse_and_validate_html(zip_.read(html_file), html_file, scripts_allowed,
                                                            scripts_allowed, files)
    return pokes, html, branding_type, meta_properties


def _add_meta_data(zip_, admin_user):
    m = """Uploaded by: %s
    Uploaded on: %s
    """ % (admin_user.email().encode("utf8"), time.strftime("%a, %d %b %Y %H:%M:%S %Z"))

    zip_.writestr(ROGERTHAT_META_INFO_FILE, m)


@returns(Branding)
@arguments(app_id=unicode, base64_str=unicode)
def save_core_branding(app_id, base64_str):
    app = get_app(app_id)
    try:
        zip_stream = StringIO()
        zip_stream.write(base64.b64decode(base64_str))
        zip_stream.seek(0)
        _zip = ZipFile(zip_stream)
    except BadZipfile as e:
        raise BadBrandingZipException(e.message)
    branding = store_branding_zip(None, _zip, u'Core branding of %s' % app_id)
    app.core_branding_hash = branding.hash
    app.put()
    return branding
