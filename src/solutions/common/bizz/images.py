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
import logging

import cloudstorage
from cgi import FieldStorage
from google.appengine.ext import ndb
from google.appengine.ext.deferred import deferred
from google.appengine.ext.ndb.key import Key
from mimetypes import guess_extension
from typing import List, Iterable, Tuple, Union

from mcfw.exceptions import HttpBadRequestException
from oca_imaging import generate_scaled_images, ImageRequest, ResizedImage
from rogerthat.bizz.maps.poi.models import PointOfInterest
from rogerthat.consts import DEBUG
from rogerthat.dal import parent_ndb_key
from rogerthat.models.news import MediaType
from rogerthat.models.settings import ServiceInfo, MediaItem
from rogerthat.models.utils import ndb_allocate_id
from rogerthat.rpc import users
from rogerthat.to.messaging import AttachmentTO
from rogerthat.utils import read_file_in_chunks
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks
from rogerthat.utils.service import get_service_identity_tuple
from solutions import SOLUTION_COMMON
from solutions.common.consts import OCA_FILES_BUCKET, get_files_bucket
from solutions.common.models.forms import UploadedFile, ScaledImage


def upload_file(service_user, uploaded_file, prefix, file_type, reference=None, do_generate_scaled_images=True):
    # type: (users.User, FieldStorage, str, str, Key, bool) -> UploadedFile
    content_type = uploaded_file.type
    if content_type not in AttachmentTO.CONTENT_TYPES:
        raise HttpBadRequestException('oca.attachment_must_be_of_type')
    extension = guess_extension(content_type)
    if extension == '.jpe':
        extension = '.jpeg'
    if not extension:
        raise HttpBadRequestException('oca.attachment_must_be_of_type')
    if reference and reference.kind() == PointOfInterest._get_kind():
        parent_key = reference
    else:
        parent_key = parent_ndb_key(service_user, SOLUTION_COMMON)
    file_id = ndb_allocate_id(UploadedFile, parent=parent_key)
    if not prefix:
        prefix = 'media'
    if reference and reference.kind() == PointOfInterest._get_kind():
        cloudstorage_path = '/%(bucket)s/poi/%(poi_id)d%(prefix)s/%(file_id)d%(extension)s' % {
            'bucket': OCA_FILES_BUCKET,
            'poi_id': reference.id(),
            'prefix': '' if not prefix else ('/' + prefix),
            'file_id': file_id,
            'extension': extension
        }
        key = UploadedFile.create_key_poi(reference, file_id)
    else:
        if prefix and prefix.startswith('branding'):
            do_generate_scaled_images = False
        cloudstorage_path = '/%(bucket)s/services/%(service)s%(prefix)s/%(file_id)d%(extension)s' % {
            'service': service_user.email(),
            'prefix': '' if not prefix else ('/' + prefix),
            'bucket': OCA_FILES_BUCKET,
            'file_id': file_id,
            'extension': extension
        }
        key = UploadedFile.create_key_service(service_user, file_id)
    uploaded_file.file.seek(0, 2)
    size = uploaded_file.file.tell()
    uploaded_file.file.seek(0)
    file_model = UploadedFile(key=key,
                              reference=reference,
                              content_type=content_type,
                              size=size,
                              type=file_type,
                              cloudstorage_path=cloudstorage_path)
    with cloudstorage.open(file_model.cloudstorage_path, 'w', content_type=content_type) as f:
        for chunk in read_file_in_chunks(uploaded_file.file):
            f.write(chunk)
    if do_generate_scaled_images and file_type in (MediaType.IMAGE, MediaType.IMAGE_360):
        try:
            logging.debug('Generating scaled images for uploaded file %d', file_id)
            image_requests = get_image_requests_for_file(file_model)
            results = generate_scaled_images(file_model.original_url, image_requests)
            file_model.scaled_images = _get_scaled_images(image_requests, results)
        except Exception as e:
            # no panic, we'll deal with it later
            logging.warning(e, exc_info=True)
            deferred.defer(_generate_scaled_images_for_uploaded_file, file_model.key)
    file_model.put()
    return file_model


def get_image_requests_for_file(file_model):
    if file_model.type == MediaType.IMAGE:
        max_size = 720 if DEBUG else 1920
    elif file_model.type == MediaType.IMAGE_360:
        max_size = 1920 if DEBUG else 4000
    else:
        raise NotImplementedError('Unexpected file type %s' % file_model.type)
    # Remove bucket and filename from path
    base_path = file_model.cloudstorage_path.split('/', 2)[2].rsplit('/', 1)[0]
    bucket = get_files_bucket()
    extension = '.png' if file_model.content_type == 'image/png' else '.jpeg'
    return [
            ImageRequest(content_type=file_model.content_type,
                         quality=90,
                         max_size=500,
                         bucket=bucket,
                         filename='%s/scaled/%d-%s%s' % (base_path, file_model.id, 'thumb', extension)),
            ImageRequest(content_type=file_model.content_type,
                         quality=90,
                         max_size=max_size,
                         bucket=bucket,
                         filename='%s/scaled/%d-%s%s' % (base_path, file_model.id, 'large', extension)),
        ]


def _get_scaled_images(requests, results):
    # type: (List[ImageRequest], List[ResizedImage]) -> List[ScaledImage]
    return [
        ScaledImage(cloudstorage_path='/%s/%s' % (request.bucket, result.path),
                    width=result.width,
                    height=result.height,
                    size=result.size,
                    content_type=result.content_type)
        for request, result in zip(requests, results) if result
    ]


def _generate_scaled_images_for_uploaded_file(file_key):
    # type: (ndb.Key) -> None
    file_model = file_key.get()  # type: UploadedFile
    if not file_model:
        logging.debug('File not found, not generating scaled images: %s', file_key)
        return
    requests = get_image_requests_for_file(file_model)
    results = generate_scaled_images(file_model.original_url, requests)
    file_model.scaled_images = _get_scaled_images(requests, results)
    if file_model.scaled_images:
        file_model.put()
    set_scaled_images_from_uploaded_files([file_model], file_model.key.parent())


def set_scaled_images_from_uploaded_files(file_models, parent_key):
    # type: (List[UploadedFile], Key) -> None
    """Change media uploaded using UploadedFile to include use thumbnails and the scaled down image
     instead of the original image"""
    # key = parent_key() or PointOfInterest key
    changed = False
    if parent_key.kind() == SOLUTION_COMMON:
        service_user, service_identity = get_service_identity_tuple(users.User(parent_key.id()))
        service_info = ServiceInfo.create_key(service_user, service_identity).get()  # type: ServiceInfo
        for file_model in file_models:
            for i, media in enumerate(service_info.media):
                if media.file_reference == file_model.key:
                    service_info.media[i] = MediaItem.from_file_model(file_model)
                    changed = True
        if changed:
            service_info.put()
    else:
        point_of_interest = parent_key.get()  # type: PointOfInterest
        if not point_of_interest:
            # Must've been deleted in the meantime
            logging.debug('Nothing to do: point of interest with key %s does not exist', parent_key)
            return
        assert isinstance(point_of_interest, PointOfInterest)
        for file_model in file_models:
            for i, media in enumerate(point_of_interest.media):
                if media.file_reference == file_model.key:
                    point_of_interest.media[i] = MediaItem.from_file_model(file_model)
                    changed = True
        if changed:
            point_of_interest.put()


def list_files(service_user, media_type, prefix=None, reference_type=None, reference=None):
    # type: (users.User, str, str, unicode, long) -> List[UploadedFile]
    if reference_type == 'point_of_interest':
        ref_key = PointOfInterest.create_key(reference)
        qry = UploadedFile.list_by_poi(ref_key)
    elif prefix:
        path = '/%(bucket)s/services/%(service)s/%(prefix)s' % {'bucket': OCA_FILES_BUCKET,
                                                                'service': service_user.email(),
                                                                'prefix': prefix}
        qry = UploadedFile.list_by_user_and_path(service_user, path)
    else:
        qry = UploadedFile.list_by_user(service_user)  # type: Iterable[UploadedFile]
    # TODO: maybe add 3 indexes for this instead / use search index
    return [item for item in qry if item.type == media_type]


def remove_files(keys):
    # type: (List[ndb.Key]) -> None
    to_remove = ndb.get_multi(keys)  # type: List[UploadedFile]
    tasks = [create_task(_delete_from_gcs, uploaded_file.cloudstorage_path) for uploaded_file in to_remove]
    schedule_tasks(tasks)
    ndb.delete_multi(keys)


def _delete_from_gcs(cloudstorage_path):
    try:
        cloudstorage.delete(cloudstorage_path)
    except cloudstorage.NotFoundError:
        pass
