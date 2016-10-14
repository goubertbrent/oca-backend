#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

import sys, xml
from xml.dom import minidom
import base64

def parser(lines):
    request = None
    logs = None
    log = None
    for l in lines:
        if not l[0] == '\t':
            if request:
                if log:
                    logs.append(log)
                yield request, logs
            request = l
            logs = list()
            log = None
        else:
            if l[1] in ('1','2','3','4','5'):
                if log:
                    logs.append(log)
                log = dict()
                log['severity'] = int(l[1])
                log['timestamp'] = float(l[3:20])
                log['message'] = l[21:]
            else:
                log['message'] += l[3:]
    if log:
        logs.append(log)
    yield request, logs
    
def printDecodedMessage(message):
    message = message.splitlines()
    print message[0]
    try:
        doc = minidom.parseString(''.join(message[1:]))
        for elem in doc.getElementsByTagNameNS("mobicage:comm", "c"):
            print "CALL  ", elem.getAttribute("i"), base64.decodestring(elem.firstChild.nodeValue)
        for elem in doc.getElementsByTagNameNS("mobicage:comm", "r"):
            print "RESULT", elem.getAttribute("i"),  base64.decodestring(elem.firstChild.nodeValue)
        for elem in doc.getElementsByTagNameNS("mobicage:comm", "a"):
            print "ACK   ", elem.getAttribute("i")
    except xml.parsers.expat.ExpatError: #@UndefinedVariable
        print "ERROR xml node incomplete"
        print '\n'.join(message[1:])
    
if __name__ == '__main__':
    for r,logs in parser(sys.stdin.readlines()):
        print r.strip()
        for l in logs:
            message = l['message'].strip()
            if message.startswith("Incoming message from "):
                printDecodedMessage(message)
            elif message.startswith("Sending message to "):
                printDecodedMessage(message)
            else:
                print message
            print
        print
