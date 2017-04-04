#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.3@@

import socket
import hashlib
import random

def test(ip, port):

    username = "1b4ee50a-fe03-11df-93d8-e3b36dd6d02a@mc-tracker.com"
    password = "9ebbfc3f-e75f-4a7d-ac13-b7ef84720d432d6ea940-10df-4bef-bd46-41801068f704"
    #reqidbytes = [186, 70, 186, 110, 47, 153, 0, 216, 159, 4, 15, 188, 196, 116, 113, 162]
    reqidbytes = [random.randint(0, 255) for i in range(16)]

    reqversion = '\x01'
    reqtype = '\x01'
    reqid = ''.join(map(chr, reqidbytes))
    if (len(reqid) != 16):
        print "WRONG REQID SIZE ", len(reqid)
        return
    resource = 'mobicage'
    secret = "Mobicage's mc-tracker will concer the world!"

    peekkey = hashlib.sha256(username + "@" + password).digest() 
    request = reqversion + reqtype + reqid + peekkey + chr(len(resource)) + resource
    signature = hashlib.sha256(password + secret + request).digest()
    request = request + signature

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(5) # seconds
    s.sendto(request, (ip, port))
    response = s.recv(8192)
    s.close()

    answer = response[18]

    if (response[0:2] == "\x01\x01"):
        print "Response version and type OK"
    else:
        print "Response version or type sux"

    if (reqid == response[2:18]):
        print "Response requestID OK"
    else:
        print "Response requestID sux"

    response_signature_buffer = password + secret + reqid + answer
    #print map(ord, response_signature_buffer)

    expected_signature = hashlib.sha256(password + secret + reqid + answer).digest()
    if (expected_signature == response[-32:]):
        print "Response signature OK"
    else:
        print "Response signature sux"

    print "Response answer is [" + answer + "]"

if __name__ == "__main__":
    test("jabber1.mc-tracker.com", 31415)
