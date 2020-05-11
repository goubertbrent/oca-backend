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

import argparse
import logging
import os
import pprint
import sys

import yaml


APP_ID_ROGERTHAT = 'rogerthat'


def list_top_dirs(path):
    files_and_dirs = os.listdir(path)

    def is_dir(name):
        return os.path.isdir(os.path.join(path, name))

    return filter(is_dir, files_and_dirs)


def get_service_mail_from_yaml(app_id, build_file_path):
    try:
        with open(build_file_path) as f:
            config = yaml.load(f.read())
            return config['APP_CONSTANTS']['APP_EMAIL']
    except IOError:
        logging.debug('build.yaml is not there, app_id=%s', app_id)
    except yaml.error.YAMLError:
        logging.debug('cannot parse build.yaml, app_id=%s', app_id)
    except KeyError:
        logging.debug('cannot get service mail from build.yaml app_id=%s', app_id)


def get_app_service_emails(apps_dir):
    app_ids = map(str.strip, list_top_dirs(apps_dir))
    service_emails = {}

    for app_id in app_ids:
        if app_id != APP_ID_ROGERTHAT:
            path = os.path.join(apps_dir, app_id, 'build.yaml')
            service_email = get_service_mail_from_yaml(app_id, path)
            if service_email:
                service_emails[app_id] = service_email

    return service_emails

def main(apps_dir, debug):
    if not apps_dir:
        raise Exception('Please provide the apps directory')

    if not list_top_dirs(apps_dir):
        raise Exception('Empty apps directory')

    if debug:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    service_emails = get_app_service_emails(apps_dir)
    if service_emails:
        pp = pprint.PrettyPrinter(width=5)
        pp.pprint(service_emails)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Print the app ids with their service email as dict")
    parser.add_argument('-d', '--apps_dir', help="Apps directory")
    parser.add_argument('-l', '--log_debug', help="Print debug messages", action='store_true')
    args = parser.parse_args()

    try:
        main(args.apps_dir, args.log_debug)
    except Exception as e:
        print 'Error,', e
