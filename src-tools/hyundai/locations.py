#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import csv
import time
import urllib
import urllib2

root_url = "http://maps.googleapis.com/maps/api/geocode/json?"

def geocode(addr):
    time.sleep(2)
    #encode our dictionary of url parameters
    params = dict(address=addr, sensor='false')
    data = urllib.urlencode(params)
    #set up our request
    url = root_url + data
    req = urllib2.Request(url)
    #make request and read response
    response = urllib2.urlopen(req)
    geodat = json.loads(response.read())
    response.close()
    #handle the data returned from google
    status = geodat['status']
    if status == 'OK':
        location = geodat['results'][0]['geometry']['location']
        return {'status':status, 'lat':location['lat'], 'lng':location['lng']}
    else:
        return {'status':status}

with open('Hyundai.csv', 'rb') as csvfile:
    r = csv.reader(csvfile, delimiter=',', quotechar='"')
    first_row = None
    for row in r:
        if not first_row:
            first_row = row
            print '"Identity","lat","lng"'
            continue
        d = dict(zip(first_row, row))

        identifier = d['Identity']
        keywords = d['Keywords'].replace(',', '')
        street = d['Adres']
        post_code = d['PC']
        city = d['Gemeente']

        address = "%s, %s %s" % (street, post_code, city)

        r = geocode(address)
        if r['status'] == 'OK':
            print '"%s","%s","%s"' % (identifier, r['lat'], r['lng'])
        else:
            print "ERROR: %s (%s)" % (r['status'], address)
            print '"%s","%s","%s"' % (identifier, '', '')
