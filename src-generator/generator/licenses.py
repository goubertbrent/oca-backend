# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

def get_license(license_text, target):
    if target == "android":
        return java_license(license_text)
    if target == "iphone":
        return objc_license(license_text)
    if target == "csharp":
        return csharp_license(license_text)
    if target == "service_api_metadata":
        return ""
    if target == 'typescript':
        return ''
    raise NotImplementedError("Licenses are not yet implemented for target '%s'" % target)


def java_license(license_):
    from StringIO import StringIO
    s = StringIO()
    s.write("/*")
    for line in license_.splitlines():
        line = line.strip()
        if line == "":
            s.write("\n *")
        else:
            s.write("\n * ")
            s.write(line)
    s.write("\n */")
    return s.getvalue()


def objc_license(license_):
    return java_license(license_)


def csharp_license(license_):
    from StringIO import StringIO
    s = StringIO()
    for line in license_.splitlines():
        line = line.strip()
        if line == "":
            s.write("\n//")
        else:
            s.write("\n// ")
            s.write(line)
    return s.getvalue()
