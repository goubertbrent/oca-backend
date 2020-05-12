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

from google.appengine.ext import db
import mc_unittest
from rogerthat.models import CompressedIntegerListExpando



class TestCase(mc_unittest.TestCase):
    l = [1, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1]

    def setUp(self, datastore_hr_probability=0):
        mc_unittest.TestCase.setUp(self, datastore_hr_probability=datastore_hr_probability)

        class MyModel(db.Expando):
            pass

        m = MyModel(key_name='test')
        m.test = TestCase.l
        m.put()

    def test_get_custom_prop(self):
        class MyModel(CompressedIntegerListExpando):
            _attribute_prefix = 'test'

        m = MyModel.get_by_key_name('test')
        self.assertListEqual(TestCase.l, m.test)

        dict_repr = db.to_dict(m)
        self.assertTrue(isinstance(dict_repr['test'], basestring))

    def test_append(self):
        class MyModel(CompressedIntegerListExpando):
            _attribute_prefix = 'test'

        m = MyModel.get_by_key_name('test')
        m.test.append(5)
        m.put()

        m = MyModel.get_by_key_name('test')
        self.assertListEqual(TestCase.l + [5], m.test)

    def test_ljust(self):
        class MyModel(CompressedIntegerListExpando):
            _attribute_prefix = 'test'

        m = MyModel.get_by_key_name('test')
        print 'Before: %r' % m.test
        m.test.ljust(5, 0, 10)  # will append 5 zeroes, and limit the number of entries to 10
        print 'After: %r' % m.test
        expected = (TestCase.l + 5 * [0])[-10:]  # [1, 0, 0, 0, 1, 0, 0, 0, 0, 0]
        print 'Expected: %r' % expected
        m.put()

        m = MyModel.get_by_key_name('test')
        self.assertListEqual(expected, m.test)
