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

from datetime import datetime, date

from google.appengine.api import users
from google.appengine.ext import ndb

from statistics.to import TO


class NdbModel(ndb.Model):
    NAMESPACE = None

    def __init__(self, *args, **kwargs):
        if not kwargs.get('key'):
            kwargs['namespace'] = self.NAMESPACE
        super(NdbModel, self).__init__(*args, **kwargs)

    def _convert_properties(self, prop):
        # type: (object) -> object
        if isinstance(prop, list):
            for index, p in enumerate(prop):
                prop[index] = self._convert_properties(p)
        elif isinstance(prop, users.User):
            return prop.email()
        elif isinstance(prop, datetime):
            return prop.isoformat().decode('utf-8') + u'Z'
        elif isinstance(prop, date):
            return prop.isoformat().decode('utf-8')
        elif isinstance(prop, ndb.GeoPt):
            return {'lat': prop.lat, 'lon': prop.lon}
        elif isinstance(prop, ndb.Key):
            id_ = prop.id()
            if isinstance(id_, str):
                return id_.decode('utf-8')
            return id_
        elif isinstance(prop, dict):
            for p in prop:
                prop[p] = self._convert_properties(prop[p])
        elif isinstance(prop, ndb.Expando):
            return self._convert_properties(prop.to_dict())
        elif isinstance(prop, TO):
            return prop.to_dict()
        return prop

    def to_dict(self, extra_properties=None, include=None, exclude=None):
        """
            Converts the model to a JSON serializable dictionary

        Args:
            extra_properties (list[unicode]): Extra properties to add that are present as an @property of the model
            include(set): Optional set of property names to include, default all.
            exclude(set): Optional set of property names to skip, default none.
        Returns:
            dict
        """
        exclude = exclude or []
        if not extra_properties:
            extra_properties = []
        if 'id' not in exclude:
            extra_properties.append('id')
        result = super(NdbModel, self).to_dict(include=include, exclude=exclude)
        for p in extra_properties:
            if hasattr(self, p):
                result[p] = getattr(self, p)
        return self._convert_properties(result)

    @classmethod
    def query(cls, *args, **kwargs):
        kwargs['namespace'] = kwargs.get('namespace', cls.NAMESPACE)
        return super(NdbModel, cls).query(*args, **kwargs)

    @classmethod
    def get_by_id(cls, id, parent=None, **ctx_options):
        return super(NdbModel, cls).get_by_id(id, parent=parent, namespace=cls.NAMESPACE, **ctx_options)

    @classmethod
    def get_or_insert(cls, *args, **kwds):
        return super(NdbModel, cls).get_or_insert(*args, namespace=cls.NAMESPACE, **kwds)