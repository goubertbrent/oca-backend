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

import os

import base64
import jinja2
import logging
import webapp2
from contextlib import closing
from google.appengine.ext import webapp, db
from jinja2 import Undefined, DebugUndefined
from lxml import html, etree
from zipfile import ZipFile

from rogerthat.consts import MAX_BRANDING_PDF_SIZE, DEBUG
from rogerthat.dal import parent_key, put_and_invalidate_cache
from rogerthat.rpc import users
from rogerthat.service.api import system
from rogerthat.templates.jinja_htmlcompress import HTMLCompress
from rogerthat.utils.channel import broadcast_via_iframe_result, send_message
from solutions import translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import broadcast_updates_pending, put_pdf_branding
from solutions.common.dal import get_solution_main_branding, get_solution_settings, get_solution_identity_settings
from solutions.common.models.static_content import SolutionStaticContent
from solutions.common.utils import is_default_service_identity
from solutions.jinja_extensions import TranslateExtension

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader([os.path.join(os.path.dirname(__file__), '..', 'templates')]),
    undefined=DebugUndefined if DEBUG else Undefined,
    extensions=[TranslateExtension])

# Prefer to use this one, automatically removes unnecessary whitespace
JINJA_COMPRESSED_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader([os.path.join(os.path.dirname(__file__), '..', 'templates')]),
    undefined=DebugUndefined if DEBUG else Undefined,
    extensions=[TranslateExtension, HTMLCompress])


class ImageViewerHandler(webapp2.RequestHandler):

    def get(self):
        picture_url = self.request.get('p')
        if not picture_url:
            self.redirect("/ourcityapp")
            return
        jinja_template = JINJA_ENVIRONMENT.get_template('image_viewer.html')
        self.response.out.write(jinja_template.render({'picture_url': picture_url}))


class SolutionMainBrandingHandler(webapp2.RequestHandler):

    def get(self, page):
        service_user = users.get_current_user()
        session_ = users.get_current_session()
        service_identity = session_.service_identity
        _, extension = os.path.splitext(page.lower())
        if extension in (".jpg", ".jpeg"):
            self.response.headers['Content-Type'] = "image/jpeg"
        elif extension == ".png":
            self.response.headers['Content-Type'] = "image/png"
        elif extension == ".css":
            self.response.headers['Content-Type'] = "text/css"

        main_branding = get_solution_main_branding(service_user)
        with closing(ZipFile(StringIO(main_branding.blob))) as zip_file:
            try:
                content = zip_file.read(page)
            except KeyError:
                if page == 'avatar.jpg':
                    self.abort(404)
                else:
                    raise

        if page == 'branding.html':
            doc = html.fromstring(content)
            sln_i_settings = None
            for elem in doc.xpath("//nuntiuz_identity_name"):
                if not sln_i_settings:
                    if is_default_service_identity(service_identity):
                        sln_i_settings = get_solution_settings(service_user)
                    else:
                        sln_i_settings = get_solution_identity_settings(service_user, service_identity)
                parent = elem.getparent()
                elem.drop_tree()
                parent.text = sln_i_settings.name
            content = etree.tostring(doc)  # @UndefinedVariable

        self.response.out.write(content)


class UploadStaticContentPDFHandler(webapp.RequestHandler):

    def post(self):
        from PyPDF2.pdf import PdfFileReader
        service_user = users.get_current_user()
        sln_settings = get_solution_settings(service_user)
        try:
            position = self.request.POST.get('position')
            icon_label = self.request.POST.get('icon_label')
            icon_name = self.request.POST.get('icon_name')
            pdf_upload = self.request.POST.get('pdf_upload')
            static_content_id = self.request.POST.get('static_content_id')
            if static_content_id:
                static_content_id = int(static_content_id)
            visible = self.request.POST.get('static_content_visible_pdf') == 'on'

            coords = map(int, position.split(','))

            if not static_content_id and pdf_upload == "":
                error = translate(sln_settings.main_language, 'PDF is required')
                self.response.out.write(broadcast_via_iframe_result(u'solutions.common.static_content.pdf.post_result',
                                                                    error=error))
                return

            if pdf_upload == "":
                branding_hash = None
            else:
                if pdf_upload.type != "application/pdf":
                    error = translate(sln_settings.main_language, 'PDF not of correct type.')
                    self.response.out.write(broadcast_via_iframe_result(u'solutions.common.static_content.pdf.post_result',
                                                                        error=error))
                    return

                pdf_stream = pdf_upload.file

                pdf_stream.seek(0)
                # Test if the file is a valid PDF
                try:
                    error_stream = StringIO()  # get rid the of zero index warnings
                    doc = PdfFileReader(pdf_stream, strict=False, warndest=error_stream)
                    logging.debug("Uploaded pdf contains %s pages", doc.numPages)
                    del doc
                except:
                    error = translate(sln_settings.main_language, 'uploaded-file-not-a-pdf')
                    self.response.out.write(broadcast_via_iframe_result(u'solutions.common.static_content.pdf.post_result',
                                                                        error=error))
                    return

                # Test if the file is not too large
                pdf_stream.seek(0)
                pdf_bytes = pdf_stream.read()
                if len(pdf_bytes) > MAX_BRANDING_PDF_SIZE:
                    error = translate(sln_settings.main_language, 'pdf-size-too-large')
                    self.response.out.write(broadcast_via_iframe_result(u'solutions.common.static_content.pdf.post_result',
                                                                        error=error))
                    return

                branding_hash = put_pdf_branding(u"Static content pdf: %s" % icon_label, base64.b64encode(pdf_bytes)).id

            def trans():
                if static_content_id:
                    sc = SolutionStaticContent.get(SolutionStaticContent.create_key(service_user, static_content_id))
                    if not sc:
                        logging.error(
                            u"Failed to update static content with id '%s' for user %s", static_content_id, service_user)
                        return sln_settings

                    if sc.old_coords != coords and sc.provisioned:
                        sc.old_coords = sc.coords
                else:
                    sc = SolutionStaticContent(parent=parent_key(sln_settings.service_user, SOLUTION_COMMON))
                    sc.old_coords = coords

                sc.icon_label = icon_label
                sc.icon_name = icon_name
                sc.text_color = None
                sc.background_color = None
                sc.html_content = None
                sc.sc_type = SolutionStaticContent.TYPE_PDF
                sc.visible = visible
                sc.coords = coords
                sc.provisioned = False
                sc.deleted = False
                if branding_hash:
                    sc.branding_hash = branding_hash

                sln_settings.updates_pending = True
                put_and_invalidate_cache(sc, sln_settings)
                return sln_settings

            xg_on = db.create_transaction_options(xg=True)
            sln_settings = db.run_in_transaction_options(xg_on, trans)
            send_message(service_user, "solutions.common.service_menu.updated")
            broadcast_updates_pending(sln_settings)
            self.response.out.write(
                broadcast_via_iframe_result(u'solutions.common.static_content.pdf.post_result', success=True))
        except:
            logging.exception(
                'Error while trying to save static content PDF for user %s' % sln_settings.service_user.email())
            self.response.out.write(broadcast_via_iframe_result(u'solutions.common.static_content.pdf.post_result',
                                                                error=translate(sln_settings.main_language,
                                                                                'error-occured-unknown')))


class FlowStatisticsExportHandler(webapp2.RequestHandler):

    def get(self):
        excel = base64.b64decode(system.export_flow_statistics())
        self.response.headers['Content-Type'] = 'application/vnd.ms-excel'
        self.response.headers['Content-Disposition'] = 'attachment; filename=Flow statistics.xls'
        self.response.write(excel)
