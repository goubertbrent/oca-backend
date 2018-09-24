# -*- coding: utf-8 -*-
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
# @@license_version:1.4@@

import os

os.environ['APPLICATION_ID'] = 'mobicagecloud'
os.environ['SERVER_NAME'] = 'localhost'
os.environ['SERVER_PORT'] = '8080'
os.environ['SERVER_SOFTWARE'] = 'Development Server'
os.environ["DEFAULT_VERSION_HOSTNAME"] = 'mobicagecloudhr.appspot.com'
os.environ['APPENGINE_RUNTIME'] = 'python27'  # Needed to make webapp.template load ._internal.django


def init_env():
    from google.appengine.api import datastore_file_stub, apiproxy_stub_map, user_service_stub, mail_stub, urlfetch_stub
    from google.appengine.api.app_identity import app_identity_stub
    from google.appengine.api.blobstore import blobstore_stub, file_blob_storage
    from google.appengine.api.images import images_stub
    from google.appengine.api.memcache import memcache_stub
    from google.appengine.api.taskqueue import taskqueue_stub
    try:

        if not apiproxy_stub_map.apiproxy.GetStub('user'):
            apiproxy_stub_map.apiproxy.RegisterStub('user', user_service_stub.UserServiceStub())
            apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3',
                                                    datastore_file_stub.DatastoreFileStub('mobicagecloud', '/dev/null',
                                                                                          '/dev/null'))
            apiproxy_stub_map.apiproxy.RegisterStub('mail', mail_stub.MailServiceStub())
            apiproxy_stub_map.apiproxy.RegisterStub('blobstore', blobstore_stub.BlobstoreServiceStub(
                file_blob_storage.FileBlobStorage('/dev/null', 'mobicagecloud')))
            apiproxy_stub_map.apiproxy.RegisterStub('memcache', memcache_stub.MemcacheServiceStub())
            apiproxy_stub_map.apiproxy.RegisterStub('images', images_stub.ImagesServiceStub())
            apiproxy_stub_map.apiproxy.RegisterStub('urlfetch', urlfetch_stub.URLFetchServiceStub())
            apiproxy_stub_map.apiproxy.RegisterStub('taskqueue', taskqueue_stub.TaskQueueServiceStub())
            apiproxy_stub_map.apiproxy.RegisterStub('app_identity_service', app_identity_stub.AppIdentityServiceStub())

    except Exception as e:
        print e
        raise

    from rogerthat.settings import get_server_settings

    settings = get_server_settings()
    settings.jabberDomain = "localhost"
