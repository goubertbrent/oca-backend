#!/usr/bin/python
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
import re
import sys

import oca_unittest
from rogerthat.translations import DEFAULT_LANGUAGE
from shop.translations import shop_translations
from solutions import translations

PATH_END_DEV = os.path.join('src-test', 'test', 'i18n')
VALID_PATH_ENDINGS = [PATH_END_DEV]

EXCLUDED_CODE_TRANSLATION_KEYS = set([
])


class I18nTest(oca_unittest.TestCase):

    def test_sln_placeholders(self):
        from rogerthat_tests.i18n.test_i18n import Test as RogerthatI18nTest
        RogerthatI18nTest._test_placeholder(self, translations)

    def test_shop_placeholders(self):
        from rogerthat_tests.i18n.test_i18n import Test as RogerthatI18nTest
        RogerthatI18nTest._test_placeholder(self, shop_translations)


    def get_src_dir(self):
        src_is_ok = False
        for path_ending in VALID_PATH_ENDINGS:
            src_is_ok = src_is_ok or os.path.split(__file__)[0].endswith(path_ending)
        self.assert_(src_is_ok, 'Wrong path: %s' % os.path.split(__file__)[0])
        src_dir = os.path.normpath(os.path.join(__file__, '..', '..', '..', '..', 'src'))
        self.assert_(os.path.isdir(src_dir), "Couldn't find src dir - tried: %s" % src_dir)
#         print 'get_src_dir: => %s' % src_dir
        return src_dir

    def do_test_code(self, translate_function_name, matcher):
        from rogerthat_tests.i18n.test_i18n import Test as RogerthatI18nTest
        if sys.platform == "win32":
            return

        def _get_translation_keys(filename):
            if filename.endswith(".pyc"):
                return
            if filename.endswith(".py"):
                return
            f = open(filename, "rb")
            try:
                source_code = f.read()
            finally:
                f.close()

            for groups in matcher.findall(source_code):
                key = groups[2].replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
                keys_found_in_code.add(unicode(key))

        def _scan_dir(path):
#             print '_scan_dir: -> %s' % path
            for f in os.listdir(path):
                filename = os.path.join(path, f)
                if os.path.isfile(filename):
                    _get_translation_keys(filename)
                else:
                    if f.startswith("."):
                        continue
                    _scan_dir(filename)

        def _should_process(path):
            ignored = [os.path.join('src', 'solutions', '__init__.py'),
                       os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src', 'lib')),
                       os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src', 'rogerthat')),
                       os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src', 'shop'))]
            for ign in ignored:
                if path.endswith(ign) or path.startswith(ign):
#                     print '_should_process: FALSE -> %s' % path
                    return False
#             print '_should_process: TRUE -> %s' % path
            return True

        import ast
        testself = self

        class MyVisitor(ast.NodeVisitor):

            def visit_Call(self, node):
                if hasattr(node.func, 'id') and node.func.id == translate_function_name:
                    testself.assert_(len(node.args) >= 2, "Illegal number of args for %s\nfile: %s:%d" %
                                     (ast.dump(node), self.current_python_file, node.lineno))
                    key_object = node.args[1]
                    if isinstance(key_object, ast.Name):
                        allowed = ('k', 'msg', 'key', 'translation_key', 'result', 'label', 'status')
                        testself.assertIn(key_object.id, allowed,
                                          '%s not in %s in %s:%s' % (key_object.id, allowed,
                                                                     self.current_python_file, node.lineno))
                    else:
                        try:
                            key = key_object.s
                        except:
                            errormsg = 'Error in %s:%s' % (self.current_python_file, node.lineno)
                            print errormsg
                            file_errors.append(errormsg)
                            return
#                             testself.assert_(False, errormsg)

                        substitutions = set()
                        for keyword in node.keywords:
                            if keyword.arg in ('_duplicate_backslashes',):
                                continue
                            substitutions.add(keyword.arg)
                        testself.assert_(re.match(
                            '^\s.*', key) == None, 'leading whitespace forbidden in [%s] - File %s:%d' % (key, self.current_python_file, node.lineno))
                        testself.assert_(re.match(
                            '.*\s$', key) == None, 'trailing whitespace forbidden in [%s] - File %s:%d' % (key, self.current_python_file, node.lineno))
                        testself.assert_(key in translations[
                                         DEFAULT_LANGUAGE], 'String in code but not in default language map: [%s] - File %s:%d' % (key, self.current_python_file, node.lineno))
                        expected_substitutions = set(
                            map(lambda x: x[0], RogerthatI18nTest._parse_placeholders(testself, translations[DEFAULT_LANGUAGE][key])))
                        testself.assert_(substitutions == expected_substitutions, '\n\nUnexpected substitution:\n  File: %s:%d\n  Key: %s\n  Code args: %s\n  Substitutions: %s' % (
                            self.current_python_file, node.lineno, key, substitutions, expected_substitutions))
                        if not re.match(r'^\w+(\.\w+)+$', key):  # Filter translations of payment stuff
                            keys_found_in_code.add(key)
                ast.NodeVisitor.generic_visit(self, node)

        m = MyVisitor()
        src_dir = self.get_src_dir()
        filenames = os.popen(
            "find ""%s"" -name '*.py' | xargs grep '%s *(' | cut -d: -f1 | uniq" % (src_dir, translate_function_name)).read().splitlines()
        self.assert_(
            len(filenames) > 0, "Error: couldn't find src files with translation texts.\nIs the dir correct: %s" % src_dir)

        file_errors = []
        keys_found_in_code = set()
        for filename in filenames:
            if not _should_process(filename):
                continue
            f = open(filename, 'r')
            body = f.read()
            f.close()
            m.current_python_file = filename
            m.visit(ast.parse(body))

        if file_errors:
            self.assert_(False, file_errors)

        translated_keys = set(k for k in translations[DEFAULT_LANGUAGE].iterkeys() if '.' not in k or k.endswith('.'))

#         _scan_dir(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src", "rogerthat", "pages"))
#         _scan_dir(os.path.join(self.get_template_dir(), "generic"))
#         _scan_dir(os.path.join(self.get_template_dir(), "flows"))
        translated_keys -= EXCLUDED_CODE_TRANSLATION_KEYS

        if not keys_found_in_code == translated_keys:
            print keys_found_in_code
            diff1 = keys_found_in_code.difference(translated_keys)
            diff2 = translated_keys.difference(keys_found_in_code)
            self.assert_(not diff1, "%s keys found in code but not translated:\n%s" % (len(diff1), diff1))
            self.assert_(not diff2, "%s keys translated but not found in code:\n%s" % (len(diff2), diff2))


    def test_code_1(self):
        translate_matcher = re.compile(
            "\\{%\\s*?translate\\s+?(?P<language>[a-zA-Z0-9_]+?)\\s*?,\\s*?(?P<start>[\"\'])(?P<key>.*?)(?P=start).+?\%\}")
        self.do_test_code('translate', translate_matcher)

    def test_code_2(self):
        translate_matcher = re.compile(
            "\\{%\\s*?common_translate\\s+?(?P<language>[a-zA-Z0-9_]+?)\\s*?,\\s*?(?P<start>[\"\'])(?P<key>.*?)(?P=start).+?\%\}")
        self.do_test_code('common_translate', translate_matcher)
