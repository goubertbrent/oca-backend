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

import time
import types

from google.appengine.api.apiproxy_stub_map import UserRPC
from google.appengine.datastore.datastore_rpc import BaseConnection
from google.appengine.ext import db, ndb
from typing import List

from mcfw.properties import azzert
from mcfw.rpc import returns, arguments


@returns(int)
@arguments(qry=(db.Query, db.GqlQuery))
def delete_all(qry):
    """
    Deletes all keys which are retrieved by the passed bound Query
    
    @param qry: Bound query which returns only the keys of the objects to be deleted
    @type qry: google.appengine.ext.db.Query
    
    @return: Number of objects removed from datastore
    @rtype: int
    
    @raise ValueError: Raised when the passed qry does not returns keys
    """
    deleted_count = 0
    keys = qry.fetch(1000)
    while keys:
        if not isinstance(keys[0], db.Key):
            raise ValueError("Query is expected to return keys instead of objects")
        deleted_count += len(keys)
        db.delete(keys)
        time.sleep(1)
        keys = qry.fetch(1000)
    return deleted_count


def delete_all_models_by_query(qry):
    # type: (ndb.Query) -> None
    """Provides a fast way to delete all models filtered by a query"""
    to_delete = []  # type: List[UserRPC]
    futures = []
    for key in qry.iter(keys_only=True):
        to_delete.append(key)
        if len(to_delete) == BaseConnection.MAX_DELETE_KEYS:
            futures.extend(ndb.delete_multi_async(to_delete))
            to_delete = []
    futures.extend(ndb.delete_multi_async(to_delete))
    for rpc in futures:
        rpc.get_result()


@returns(int)
@arguments(qry=(db.Query, db.GqlQuery), function=types.FunctionType)
def run_all(qry, function):
    """
    Run all objects which are retrieved by the passed bound Query
    
    @param qry: Bound query which returns the objects to be passed as the signle argument to the passed function
    @type qry: google.appengine.ext.db.Query
    @param function: Function which will do something with a signle object retrieved by the qry
    @type function: types.FunctionType
    
    @return: Number of objects from datastore which were processed
    @rtype: int
    """
    processed_count = 0
    objects = qry.fetch(500)
    while objects:
        for o in objects:
            function(o)
            processed_count += 1
        time.sleep(1)
        objects = qry.fetch(500)
    return processed_count


@returns(db.Key)
@arguments(db_key=db.Key)
def reconstruct_key(db_key):
    '''Utility method to reconstruct a db.Key (eg. in case the application_id has changed)'''
    parent_keys = []
    pk = db_key.parent()
    while pk:
        parent_keys.append(pk)
        pk = pk.parent()

    kwargs = {}
    for pk in reversed(parent_keys):
        kwargs['parent'] = db.Key.from_path(pk.kind(), pk.id_or_name(), **kwargs)

    new_key = db.Key.from_path(db_key.kind(), db_key.id_or_name(), **kwargs)

    azzert(new_key.id_or_name() == db_key.id_or_name())
    if db_key.parent():
        azzert(new_key.parent().id_or_name() == db_key.parent().id_or_name())

    return new_key
