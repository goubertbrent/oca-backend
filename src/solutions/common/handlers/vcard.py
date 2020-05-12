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

import jinja2
import webapp2

from solutions.common.models.vcard import VCardInfo
from solutions.jinja_extensions import TranslateExtension


JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader([os.path.join(os.path.dirname(__file__), '..', 'templates')]),
                                       extensions=[TranslateExtension])

class VCardHandler(webapp2.RequestHandler):

    def get(self, user_id=''):
        vcard_info = None
        if user_id:
            vcard_info = VCardInfo.create_key(user_id).get()
            
        if vcard_info:
            first_name = vcard_info.first_name
            last_name = vcard_info.last_name
            name =vcard_info.name
            url = vcard_info.url
            image_url = vcard_info.image_url
            vcard_url = vcard_info.vcard_url
            phone_number = vcard_info.phone_number
            email_adderess = vcard_info.email_address
            job_title = vcard_info.job_title
        else:
            first_name = u'Our'
            last_name = u'City App'
            name = u'%s %s' % (first_name, last_name)
            url = u'https://oca.page.link/OurCityApp'
            image_url = u'https://storage.googleapis.com/oca-files/vcards/our_city_app.png'
            vcard_url = u'https://storage.googleapis.com/oca-files/vcards/our_city_app.vcf'
            phone_number = None
            email_adderess = u'info@ourcityapps.com'
            job_title = u'Your Mobile City App'
        
        jinja_template = JINJA_ENVIRONMENT.get_template('vcard.html')
        self.response.out.write(jinja_template.render({'url': url,
                                                       'first_name': first_name,
                                                       'last_name': last_name,
                                                       'name': name,
                                                       'image_url': image_url,
                                                       'vcard_url': vcard_url,
                                                       'phone_number': phone_number,
                                                       'email_adderess': email_adderess,
                                                       'job_title': job_title}))
