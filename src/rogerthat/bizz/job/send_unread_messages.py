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

import itertools
import json


import cloudstorage
from mapreduce.input_readers import DatastoreInputReader
from pipeline import pipeline


def unread_message_combine(key, values, previously_combined_values):
    # used in other places
    yield values + previously_combined_values


def unread_message_reduce(key, values):
    # used in other places
    json_line = json.dumps({"key":key, "value":list(itertools.chain.from_iterable(values))})
    yield "%s\n" % json_line
    
    
class CleanupGoogleCloudStorageFiles(pipeline.Pipeline):
    # used in other places

    def run(self, output):
        for filename in output:
            cloudstorage.delete(filename)


class DatastoreQueryInputReader(DatastoreInputReader):
    # used in other places
 
    @classmethod
    def _validate_filters(cls, filters, model_class):
        pass
