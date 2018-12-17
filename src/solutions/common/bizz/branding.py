import base64
import os
import re
import zipfile

from contextlib import closing
from jinja2.exceptions import TemplateNotFound
from lxml import html
from StringIO import StringIO

from mcfw.utils import Enum

from rogerthat.bizz.branding import get_branding_blob_stream
from rogerthat.utils import file_get_contents

import solutions
from solutions.common.handlers import JINJA_ENVIRONMENT


OLD_DIMENTIONS_RE = re.compile(
    "<meta\\s+property=\\\"rt:dimensions\\\"\\s+content=\\\"\\[\\d+,\\d+,\\d+,\\d+\\]\\\"\\s*/>")


BRANDINGS_BASE = os.path.join(os.path.dirname(solutions.__file__), 'common', 'templates', 'brandings')


def get_branding_resource(filename):
    return file_get_contents(os.path.join(BRANDINGS_BASE, filename))


def get_branding_template(filename):
    # jinja env alread has /common/templates in
    path = os.path.join(os.path.basename(BRANDINGS_BASE), filename)
    return JINJA_ENVIRONMENT.get_template(path)


class ResourceType(Enum):
    JAVASCRIPT = 1
    CSS = 2
    TEMPLATE = 3


class ContentNotFoundException(Exception):
    pass


class Resource(object):

    def __init__(self, name, type, content=None, **options):
        self.name = name
        self.type = type
        self.content = content
        self.options = options
        self.version = options.get('version')
        self.is_template = options.get('is_template', False)
        self.minified = options.get('minified', True)
        self.inline = options.get('inline', False)
        self.ext = options.get('ext')

    @classmethod
    def create_element(cls, name, body=None, **attrs):
        el = html.etree.Element(name)
        if body:
            el.text = body
        for k, v in attrs.iteritems():
            el.set(k, v)
        return el

    @property
    def filename(self):
        filename = self.name
        if self.version:
            filename += '-%s' % self.version
        if self.minified:
            filename += '.min'
        if self.ext:
            return '%s.%s' % (filename, self.ext)
        return filename

    @property
    def element(self):
        raise NotImplementedError


class Stylesheet(Resource):

    def __init__(self, name, content=None, **options):
        options['ext'] = 'css'
        super(Stylesheet, self).__init__(
            name, type=ResourceType.CSS, content=content, **options)

    @property
    def element(self):
        if self.inline:
            return self.create_element('style', body=self.content, type='text/css')
        return self.create_element('link', href=self.filename, rel='stylesheet', media='screen')


class Javascript(Resource):

    def __init__(self, name, content=None, **options):
        options['ext'] = 'js'
        super(Javascript, self).__init__(
            name, type=ResourceType.JAVASCRIPT, content=content, **options)

    @property
    def element(self):
        if self.inline:
            return self.create_element('script', body=self.content, type='text/javascript')
        return self.create_element('script', type='text/Javascript', src=self.filename)


class Resources(Enum):
    JQUERY_MOBILE_INLINE_PNG = Stylesheet('jquery/jquery.mobile.inline-png', version='1.4.2')
    JQUERY = Javascript('jquery/jquery', version='1.11.0')
    JQUERY_MOBILE = Javascript('jquery/jquery.mobile', version='1.4.2')
    JQUERY_TEMPLATES = Javascript('app_jquery.tmpl', content=get_branding_resource('app_jquery.tmpl.js'))
    MOMENT_WITH_LOCALES = Javascript('moment-with-locales', content=get_branding_resource('moment-with-locales.min.js'))
    ROGERTHAT = Javascript('rogerthat/rogerthat', version='1.0', minified=False)
    ROGERTHAT_API = Javascript('rogerthat/rogerthat.api', version='1.0', minified=False)
    POLYFILLS = Javascript('app_polyfills', content=get_branding_resource('app_polyfills.js'), minified=False)


class HTMLBranding(object):

    def __init__(self, main_branding, base_dir='', *resources):
        self.main_branding_stream = StringIO(main_branding.blob)
        self.main_branding_zip = zipfile.ZipFile(self.main_branding_stream)
        self.base_dir = base_dir
        self.meta = []
        self.resources = []

        map(self.add_resource, resources)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.main_branding_zip.close()
        self.main_branding_stream.close()

    def __join_path(self, filename):
        return os.path.join(self.base_dir, filename)

    def get_content(self, filename):
        path = self.__join_path(filename)
        try:
            return get_branding_resource(path)
        except IOError as ioe:
            raise ContentNotFoundException(ioe.filename)

    def render_template(self, filename, **params):
        path = self.__join_path(filename)
        try:
            return get_branding_template(path).render(params)
        except TemplateNotFound as exc:
            raise ContentNotFoundException(exc.message)

    def add_resource(self, resource, **params):
        if not resource.content:
            try:
                if resource.is_template:
                    resource.content = self.render_template(resource.filename, **params)
                else:
                    resource.content = self.get_content(resource.filename)
            except ContentNotFoundException as e:
                pass
        self.resources.append(resource)

    def add_meta(self, **attrs):
        self.meta.append(
            Resource.create_element('meta', **attrs)
        )

    @property
    def head_elements(self):
        return self.meta + [resource.element for resource in self.resources]

    def create_doc(self, branding_doc, new_body, only_replace_message=False):
        # remove previously added dimensions
        branding_doc = OLD_DIMENTIONS_RE.sub('', branding_doc)
        doc, new_body = map(html.fromstring, (branding_doc, new_body))
        head = doc.find('./head')
        head.extend(self.head_elements)

        if only_replace_message:
            old_body = doc.find('nuntiuz_message')
        else:
            old_body = doc.find('body')

        doc.replace(old_body, new_body)
        return html.tostring(doc, encoding=unicode, include_meta_content_type=True)

    def compressed(self, app_body, only_replace_message=False):
        with closing(StringIO()) as stream:
            with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as zip:
                for filename in set(self.main_branding_zip.namelist()):
                    content = self.main_branding_zip.read(filename)
                    if filename == 'branding.html':
                        filename = 'app.html'
                        content = self.create_doc(content, app_body, only_replace_message).encode('utf-8')
                    zip.writestr(filename, content)

                for resource in self.resources:
                    content = resource.content
                    if content is not None:
                        if not isinstance(content, str):
                            content = content.encode('utf-8')
                        zip.writestr(resource.filename, content)

            return base64.b64encode(stream.getvalue())
