# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
# @@license_version:1.5@@
"""
New Tab Extension for Python-Markdown
=====================================
Modify the behavior of Links in Python-Markdown to open a in a new
window. This changes the HTML output to add target="_blank" to all
generated links.
"""

from __future__ import absolute_import, unicode_literals

from markdown.extensions import Extension
from markdown.inlinepatterns import LinkInlineProcessor, LINK_RE


class NewTabExtension(Extension):

    def extendMarkdown(self, md):
        md.inlinePatterns.register(NewTabProcessor(LINK_RE, md), 'link', 165)


class NewTabProcessor(LinkInlineProcessor):

    def handleMatch(self, m, data):
        el, start, index = super(NewTabProcessor, self).handleMatch(m, data)
        el.set('target', '_blank')
        return el, start, index


def makeExtension(**kwargs):
    return NewTabExtension(**kwargs)
