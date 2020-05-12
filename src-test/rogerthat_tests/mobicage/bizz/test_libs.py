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

import mc_unittest

class Test(mc_unittest.TestCase):

    def testHtml2text(self):
        import html2text
        html_content = u'<ul><li>Line 1</li><li>Line 2</li><li>Line 3</li><li>Line 4</li>\n</ul>'
        correct_content = u'  * Line 1\n  * Line 2\n  * Line 3\n  * Line 4\n\n'
        parsed_content = html2text.html2text(html_content)
        self.assertEqual(correct_content, parsed_content)

    def testLxml(self):
        from lxml import html, etree
        html_content = u'''<html>
<head>
 <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
 <meta property="rt:style:text-color" content="#482938"/>
 <meta property="rt:style:background-color" content="#cccccc"/>
 <meta property="rt:style:menu-item-color" content="#736c62"/>
 <meta property="rt:style:show-header" content="false"/>
 <meta property="rt:style:color-scheme" content="light"/>
 <style type="text/css">
    body { padding: 0px; margin: 0px; font-family: Arial; font-size: 1em; background-color: #cccccc; color: #482938; }
    img#logo { width: 100%; }
    #header { width: 100%; text-align: center; }
    #message { margin: 0.5em; }
    #nuntiuz_identity_name_holder { text-align: center; font-weight: bold; font-size: 1.2em; }
</style>
</head>
<body>
    <div id="header">
        <img id="logo" src="logo.jpg" />
    </div>
    <div id="message">
        <div id="nuntiuz_identity_name_holder">
            <span><nuntiuz_identity_name/></span>
        </div>
    </div>
</body>
</html>
'''
        name = 'service_id_name_replaced'
        correct_content = u'<html>\n<head>\n <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>\n <meta property="rt:style:text-color" content="#482938"/>\n <meta property="rt:style:background-color" content="#cccccc"/>\n <meta property="rt:style:menu-item-color" content="#736c62"/>\n <meta property="rt:style:show-header" content="false"/>\n <meta property="rt:style:color-scheme" content="light"/>\n <style type="text/css">\n    body { padding: 0px; margin: 0px; font-family: Arial; font-size: 1em; background-color: #cccccc; color: #482938; }\n    img#logo { width: 100%; }\n    #header { width: 100%; text-align: center; }\n    #message { margin: 0.5em; }\n    #nuntiuz_identity_name_holder { text-align: center; font-weight: bold; font-size: 1.2em; }\n</style>\n</head>\n<body>\n    <div id="header">\n        <img id="logo" src="logo.jpg"/>\n    </div>\n    <div id="message">\n        <div id="nuntiuz_identity_name_holder">\n            <span>service_id_name_replaced</span>\n        </div>\n    </div>\n</body>\n</html>'

        doc = html.fromstring(html_content)
        elements = doc.xpath("//nuntiuz_identity_name")
        if elements:

            elem = elements[0]
            parent = elem.getparent()
            elem.drop_tree()
            parent.text = name
        parsed_content = etree.tostring(doc)
        self.assertEqual(correct_content, parsed_content)
