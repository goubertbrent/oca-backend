#!/usr/bin/python
# -*- coding: utf-8 -*-
# COPYRIGHT (C) 2011-2014 MOBICAGE NV
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
# @@license_version:1.7@@
import Queue
from cStringIO import StringIO
import hashlib
import httplib
import json
import os
import sys
import threading
import urllib
import urllib2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcfw.zip'))

DEBUG = True

def get_root_url(application):
    if DEBUG:
        url = "http://localhost:8080"
    else:
        url = "https://backup-server.%s.appspot.com" % application
    return url

def get_connection(application):
    if DEBUG:
        conn = httplib.HTTPConnection("localhost", 8080)
    else:
        conn = httplib.HTTPSConnection("backup-server.%s.appspot.com" % application)
    return conn

def start_persister(output_dir):
    queue = Queue.Queue()
    def run():
        print "Persister thread ready for action ..."
        files = dict()
        while True:
            task = queue.get()
            if not task:
                # Stop persister
                for f in files.values():
                    f.close()
                print "Quiting persister thread ..."
                break
            model, data = task
            if not model in files:
                files[model] = open("%s/%s" % (output_dir, model), "wb")
            files[model].write(data)
    t = threading.Thread(target=run)
    t.start()
    return queue

def start_model_grabber(application, password, model, pqueue):
    from mcfw.serialization import ds_str
    def run():
        print "Initiating backup for %s." % model
        conn = get_connection(application)
        cursor = None
        while True:
            params = dict(password=password, kind=model)
            if cursor:
                params["cursor"] = cursor
            conn.request("POST", "/backup", urllib.urlencode(params))
            response = conn.getresponse()
            if not response.status == 200:
                print "Failure backing up %s due to unexpected server response:\nStatus: %sReason: %s" % (model, response.status, response.reason)
                break
            else:
                data = response.read()
                data_size = len(data)
                checksum = hashlib.sha256(password)
                stream = StringIO(data)
                stream.seek(0)
                while stream.tell() < data_size - 1:
                    checksum.update(ds_str(stream))
                if not checksum.hexdigest() == response.getheader("X-Checksum", ""):
                    print "Failure backing up %s. Error validating checksum" % model
                    break
                pqueue.put((model, data))
                cursor = response.getheader("X-Cursor", None)
                if not cursor:
                    print "Successfully finished backing up %s." % model
                    break
        conn.close()
    t = threading.Thread(target=run)
    t.start()
    return t

def get_models(application, password):
    return json.load(urllib2.urlopen("%s/models" % get_root_url(application), urllib.urlencode(dict(password=password))))

if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser("usage %prog -a application -p password -o output")
    parser.add_option("-a", "--application", dest="app",
                      help="App Engine app id (eg mobicagecloudhr)", type="string")
    parser.add_option("-p", "--password", dest="pwd",
                      help="Password of backup server", type="string")
    parser.add_option("-o", "--output", dest="output",
                      help="Output directory", type="string")
    (options, args) = parser.parse_args()

    if not (options.app and options.pwd and options.output):
        parser.print_usage()
        exit(1)

    pqueue = start_persister(options.output)
    try:
        models = get_models(options.app, options.pwd)
        backup_threads = list()
        for model in models:
            backup_threads.append(start_model_grabber(options.app, options.pwd, model, pqueue))
        while backup_threads:
            backup_threads.pop().join()
    finally:
        pqueue.put(False)  # Stop persister

