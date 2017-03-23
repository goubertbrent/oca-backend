# -*- coding: utf-8 -*-
# COPYRIGHT (C) 2011-2016 MOBICAGE NV
# ALL RIGHTS RESERVED.
#
# ALTHOUGH YOU MAY BE ABLE TO READ THE CONTENT OF THIS FILE, THIS FILE
# CONTAINS CONFIDENTIAL INFORMATION OF MOBICAGE NV. YOU ARE NOT ALLOWED
# TO MODIFY, REPRODUCE, DISCLOSE, PUBLISH OR DISTRIBUTE ITS CONTENT,
# EMBED IT IN OTHER SOFTWARE, OR CREATE DERIVATIVE WORKS, UNLESS PRIOR
# WRITTEN PERMISSION IS OBTAINED FROM MOBICAGE NV.
#
# THE COPYRIGHT NOTICE ABOVE DOES NOT EVIDENCE ANY ACTUAL OR INTENDED
# PUBLICATION OF SUCH SOURCE CODE.
#
# @@license_version:1.9@@

# VERSION 1

import logging
import os
import shutil
import time
import subprocess
import yaml

CURRENT_DIRECTORY = os.path.realpath(os.path.dirname(__file__))
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s [BUILD] %(asctime)s %(message)s', datefmt='%Y-%d-%m %H:%M:%S')
YAML_FILES = ['app', 'cron', 'index', 'queue']
MERGE_FILES = ['rogerthat_service_api_calls.py']
KNOWN_LISTS = ['handlers', 'libraries', 'cron', 'indexes', 'queue']
KNOWN_DICTS = ['admin_console']
IGNORED_FILES = ['.DS_Store', '.pyc', '.pyo', '.yaml'] + MERGE_FILES

def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                if any(s.endswith(suffix) for suffix in IGNORED_FILES):
                    continue
                shutil.copy2(s, d)


def create_folder(filename):
    directory = os.path.realpath(os.path.join(filename, '..'))
    if not os.path.exists(directory):
        try:
            os.mkdir(directory)
        except OSError:
            pass


def is_not_list_or_dict(obj):
    return not (isinstance(obj, list) or isinstance(obj, dict))


# noinspection Restricted_Python_calls
def merge_yaml(first_file, second_file, output_file):
    create_folder(first_file)
    create_folder(second_file)
    create_folder(output_file)
    try:
        time_first_file = os.stat(first_file).st_mtime
        time_second_file = os.stat(second_file).st_mtime
    except OSError as err:
        # File not found, do nothing.
        if err.errno == 2:
            raise
        else:
            raise
    try:
        if os.path.exists(output_file):
            time_output_file = os.stat(output_file).st_mtime
        else:
            time_output_file = 0
    except OSError as err:
        if err.errno == 2:
            raise
        else:
            raise
    # Do not update this file if it hasn't been modified

    if (time_first_file > time_output_file) or (time_second_file > time_output_file):
        logging.info('Rebuilding %s', output_file)
        with open(first_file, 'r+b') as first_file_contents:
            first = yaml.load(first_file_contents)
            with open(second_file, 'r+b') as second_file_contents:
                second = yaml.load(second_file_contents)
                # Loop over closed source
                for key in second:
                    # Overwrite / copy simple properties
                    if is_not_list_or_dict(second[key]) or key not in first:
                        first[key] = second[key]
                    else:
                        # key not in first list and is a dict or list
                        if isinstance(second[key], list):
                            if key not in KNOWN_LISTS:
                                raise Exception("Unknown list %r" % key)
                            else:
                                first[key] = second[key] + first[key]
                        elif isinstance(second[key], dict):
                            if key not in KNOWN_DICTS:
                                raise Exception("Unknown dict %r" % key)
                            else:
                                for d_key in second[key].iterkeys():
                                    if isinstance(second[key][d_key], list):
                                        first[key][d_key] = second[key][d_key] + first[key][d_key]
                                    else:
                                        raise Exception('Unknown type %s %s %s' % (key, d_key, type(second[key][d_key])))

                        else:
                            raise Exception('Unknown type %s %s' % (key, type(second[key])))
                with open(output_file, 'w') as output_file_contents:
                    output_file_contents.write(yaml.safe_dump(first, default_flow_style=False))


# noinspection Restricted_Python_calls
def merge_source_files(open_source_dir, closed_source_dir, result_source_dir, open_source_name, closed_source_name):
    # Only remove the files that are no longer present in the open source or closed source folder
    for subdir, dirs, files in os.walk(result_source_dir):
        for f in files:
            if any(f.endswith(suffix) for suffix in IGNORED_FILES):
                continue
            file_path = os.path.join(subdir, f)
            closed_source_path = file_path.replace('/%s/build/' % closed_source_name,
                                                   '/%s/src/' % closed_source_name,)
            exists_in_closed_source = os.path.exists(closed_source_path)

            open_source_path = file_path.replace('/%s/build/' % closed_source_name,
                                                 '/%s/src/' % open_source_name,)
            exists_in_open_source = os.path.exists(open_source_path)
            if exists_in_closed_source and exists_in_open_source and not (
                        file_path.endswith('__init__.py') or file_path.endswith('.yaml')):
                logging.warn(
                    "File %s found in both closed source and open source projects. Closed source file will be used.",
                    file_path)
            if not (exists_in_closed_source or exists_in_open_source):
                logging.info('Refreshing file %s', file_path)
                os.remove(file_path)

    copytree(open_source_dir, result_source_dir)
    copytree(closed_source_dir, result_source_dir)
    for yaml_file in YAML_FILES:
        first_yaml = os.path.join(open_source_dir, '%s.yaml' % yaml_file)
        second_yaml = os.path.join(closed_source_dir, '%s.yaml' % yaml_file)
        output_yaml = os.path.join(result_source_dir, '%s.yaml' % yaml_file)
        merge_yaml(first_yaml, second_yaml, output_yaml)
    for merge_file in MERGE_FILES:
        first_file = os.path.join(open_source_dir, merge_file)
        second_file = os.path.join(closed_source_dir, merge_file)
        output_file = os.path.join(result_source_dir, merge_file)
        time_first_file = os.stat(first_file).st_mtime
        time_second_file = os.stat(second_file).st_mtime
        if os.path.exists(output_file):
            time_output_file = os.stat(output_file).st_mtime
        else:
            time_output_file = 0
        if (time_first_file > time_output_file) or (time_second_file > time_output_file):
            with open(first_file) as f:
                first_contents = f.read()
            with open(second_file) as f:
                second_contents = f.read()
            with open(output_file, 'w') as f:
                f.seek(0)
                f.write(first_contents)
                f.write(second_contents)
                f.truncate()


def get_git_revision_short_hash(working_dir):
    return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=working_dir).strip()


def create_versions(open_source_dir, closed_source_dir, result_source_dir):
    output = '''VERSIONS = {}
VERSIONS["rogerthat_backend"] = "%(rogerthat_backend_version)s"
VERSIONS["oca_backend"] = "%(oca_backend_version)s"''' % dict(rogerthat_backend_version=get_git_revision_short_hash(open_source_dir),
                                                              oca_backend_version=get_git_revision_short_hash(closed_source_dir))

    path = os.path.join(result_source_dir, "version")
    with open(os.path.join(path, "__init__.py"), 'w+') as f:
        f.write(output.encode('utf-8'))


if __name__ == '__main__':
    open_source_name = 'rogerthat-backend'
    closed_source_name = 'appengine'
    open_source_dir = os.path.join(CURRENT_DIRECTORY, '..', open_source_name, 'src')
    closed_source_dir = os.path.join(CURRENT_DIRECTORY, 'src')
    result_source_dir = os.path.join(CURRENT_DIRECTORY, 'build')
    t = time.time()
    merge_source_files(open_source_dir, closed_source_dir, result_source_dir, open_source_name, closed_source_name)
    create_versions(open_source_dir, closed_source_dir, result_source_dir)
    logging.info('Build in %d ms', (time.time() - t) * 1000)
