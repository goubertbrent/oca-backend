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

from contextlib import closing
import logging
import os
from zipfile import ZipFile, ZIP_DEFLATED

import cloudstorage
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import blobstore_handlers

from mcfw.properties import azzert
from rogerthat.bizz.branding import store_branding, ROGERTHAT_META_INFO_FILE, NUNTIUZ_POKE, NUNTIUZ_POKE_TAG, \
    store_branding_pdf, get_branding_blob_stream, get_branding_cloudstorage_path, replace_branding
from rogerthat.dal.app import get_app_name_by_id
from rogerthat.dal.service import get_default_service_identity
from rogerthat.exceptions.branding import BadBrandingZipException
from rogerthat.models import Branding, App
from rogerthat.rpc import users
from rogerthat.rpc.service import ServiceApiException
from rogerthat.utils import safe_file_name
from rogerthat.utils.channel import broadcast_via_iframe_result

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class BrandingDownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, hash_):
        if not hash_:
            self.error(404)
            return
        self.response.headers['Cache-Control'] = "public, max-age=31536000"  # Cache for ever (1 year)
        self.response.headers['Content-Type'] = "application/zip"
        branding = Branding.get_by_key_name(hash_)
        if branding:
            filename = "branding_%s_%s.zip" % (safe_file_name(branding.description), hash_)
            if branding.blob_key:
                gcs_filename = get_branding_cloudstorage_path(hash_, branding.user)
                self.response.headers['Content-Disposition'] = 'attachment; filename=%s' % filename
                with cloudstorage.open(gcs_filename, 'r') as gcs_file:
                    self.response.write(gcs_file.read())
            else:
                logging.error('Serving branding that is stored in the model, this should not happen anymore after the'
                              ' may 2017 migration which stores all brandings on cloudstorage')
                self.response.headers['Content-Disposition'] = 'attachment; filename=%s' % filename
                self.response.out.write(branding.blob)
        else:
            self.error(404)

    post = get


class OriginalBrandingDownloadHandler(webapp.RequestHandler):
    def get(self, hash_):
        self.response.headers['Content-Type'] = 'application/zip'
        branding = Branding.get_by_key_name(hash_)
        self.response.headers['Content-Disposition'] = 'attachment; filename=branding_%s_%s.zip' % (
        safe_file_name(branding.description), hash_)
        azzert(branding.user == users.get_current_user())
        zip_in = ZipFile(StringIO(branding.blob))

        output_zip = StringIO()

        zip_out = ZipFile(output_zip, 'w', compression=ZIP_DEFLATED)
        for file_name in set(zip_in.namelist()):
            if file_name in ['branding.html', 'branding_web.html']:
                html = zip_in.read(file_name)
                for poke in db.get(branding.pokes or []):
                    html = html.replace("%s%s" % (NUNTIUZ_POKE, poke.hash.encode('utf8')),
                                        "%s%s" % (NUNTIUZ_POKE_TAG, poke.tag.encode('utf8')))
                zip_out.writestr(file_name, html)
            elif file_name not in [ROGERTHAT_META_INFO_FILE]:
                zip_out.writestr(file_name, zip_in.read(file_name))
        zip_in.close()
        zip_out.close()

        self.response.out.write(output_zip.getvalue())


class PostBrandingHandler(webapp.RequestHandler):
    def post(self):
        service_user = users.get_current_user()
        try:
            upload = self.request.POST.get('file')
            replace = self.request.POST.get('replace', 'off') == 'on'
            logging.info("Handling file of type: " + upload.type)
            description = self.request.POST.get("description")

            stream = StringIO()
            stream.write(upload.file.read())
            if upload.type == "application/pdf":
                store_branding_pdf(service_user, stream, description)
            else:
                if replace:
                    replace_branding(service_user, stream, description)
                else:
                    store_branding(service_user, stream, description)
            self.response.out.write(broadcast_via_iframe_result(u'rogerthat.branding.post_result'))
        except ServiceApiException as e:
            extra_kwargs = dict()
            if isinstance(e, BadBrandingZipException):
                extra_kwargs['reason'] = e.fields['reason']
                extra_kwargs['solution'] = u'It is advised to use a different zip tool. Eg. 7-Zip'
            self.response.out.write(broadcast_via_iframe_result(u'rogerthat.branding.post_result', error=str(e),
                                                                error_code=e.code, **extra_kwargs))
        except:
            self.response.out.write(broadcast_via_iframe_result(u'rogerthat.branding.post_result',
                                                                error=u"Unknown error has occurred."))
            logging.exception("Failure receiving new branding ...")


class BrandingHandler(webapp.RequestHandler):
    def get(self, the_hash, page):
        self.response.headers['Cache-Control'] = "public, max-age=31536000"  # Cache forever (1 year)
        branding = Branding.get_by_key_name(the_hash)
        if not branding:
            self.error(404)
            return

        zipStream = get_branding_blob_stream(branding)
        if not zipStream:
            return self.error(404)

        with closing(zipStream):
            the_zip = ZipFile(zipStream)
            files = [fi.filename for fi in the_zip.filelist]
            if page == "branding_web.html" and page not in files:
                page = "branding.html"
            if not page in files:
                logging.warning("%s not found in branding zip" % page)
                self.error(404)
                return
            _, extension = os.path.splitext(page.lower())
            if extension in (".jpg", ".jpeg"):
                self.response.headers['Content-Type'] = "image/jpeg"
            elif extension == ".png":
                self.response.headers['Content-Type'] = "image/png"
            elif extension == ".css":
                self.response.headers['Content-Type'] = "text/css"
            content = the_zip.read(page)
        if self.request.get('xrender', 'false') == 'true':
            from lxml import html, etree
            doc = html.fromstring(content)
            elements = doc.xpath("//nuntiuz_identity_name")
            if elements:
                if branding.user:
                    si = get_default_service_identity(branding.user)
                    name = si.name
                else:
                    name = get_app_name_by_id(App.APP_ID_ROGERTHAT)
                elem = elements[0]
                parent = elem.getparent()
                elem.drop_tree()
                parent.text = name
            self.response.out.write(etree.tostring(doc))  # @UndefinedVariable
        else:
            self.response.out.write(content)
