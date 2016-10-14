#!/usr/bin/python
# -*- coding: utf-8 -*-
import csv
import os
import time
import urllib
import urllib2
import uuid
import logging

def geocode(address):
    time.sleep(2)
    # encode our dictionary of url parameters
    params = dict(address=address, sensor='false')
    data = urllib.urlencode(params)
    # set up our request
    url = "http://maps.googleapis.com/maps/api/geocode/json?" + data
    req = urllib2.Request(url)
    # make request and read response
    response = urllib2.urlopen(req)
    geodat = json.loads(response.read())
    response.close()
    # handle the data returned from google
    status = geodat['status']
    if status == 'OK':
        location = geodat['results'][0]['geometry']['location']
        return {'status':status, 'lat':location['lat'], 'lng':location['lng']}
    else:
        return {'status':status}

try:
    import json
except ImportError:
    import simplejson as json

DRY_RUN = bool(int(os.environ.get('DRY_RUN', '1')))

# API_KEY = 'ak1a45cc502e981b808ab8aee0f265875e34d358b473d22f38b42657a143e550c9'
# URL = 'http://127.0.0.1:8080/api/1'
API_KEY = 'ak7b8290bccf06fae06e8c7ded3905f6d38144d32bcd0c39f6e9314556fe4e098a'
URL = 'https://rogerth.at/api/1'
HEADERS = {
    'Content-Type': 'application/json-rpc; charset=utf-8',
    'X-Nuntiuz-API-key': API_KEY
}

DESCRIPTIONS = {
    'nl' : '''Hyundai %(name)s: maak gebruik van deze handige dienst om ons te contacteren.
Via deze dienst kan u bijvoorbeeld een afspraak, een offerte of een catalogus aanvragen en zoveel meer.

Ontdek het hier!

Hyundai - New Thinking, New Possibilities!

Hyundai %(name)s
%(address)s''',
    'fr' : '''Hyundai %(name)s: utilisez ce service afin de nous contacter.
Via ce service vous pouvez, par exemple, prendre un rendez-vous, demander une offre de prix ou un catalogue et beaucoup plus.

Découvrez-le ici !

Hyundai - New Thinking, New Possibilities!

Hyundai %(name)s
%(address)s''',
    'en': '''Hyundai %(name)s: Use this service to get in touch with our company.
Via this service you can, for example, arrange an appointment, ask a price offer, a catalogue and much more.

Discover it here !

Hyundai - New Thinking, New Possibilities!

Hyundai %(name)s
%(address)s''',
    'de': '''Hyundai %(name)s: Mit diesem Dienst können Sie uns kontaktieren.
Mit diesem Dienst können Sie zum Beispiel einen Termin vereinbaren, ein Angebot oder Katalog anzufordern und vieles mehr.

Entdecken Sie es hier!

Hyundai - New Thinking, New Possibilities!

Hyundai %(name)s
%(address)s''',
}

def guid():
    return str(uuid.uuid4())

def call_rogerthat(data):
    json_data = json.dumps(data)  # json.dumps exports by default a utf-8 encoded string
#    print 'Request:', json_data
    request = urllib2.Request(URL, json_data, HEADERS)
    response = urllib2.urlopen(request)
#    print 'Response code:', response.getcode()
#    print 'Response:', response.read()
    if response.getcode() != 200:
        raise response.getcode()
    return json.loads(response.read())

# TODO: at the end, list all identities that are not in the .csv file

# print 'SHOULD fix TODOs first'
# import sys;sys.exit(1)

print '* Listing all existing identities'
si_lr_response = call_rogerthat(dict(id=guid(),
                                     method="system.list_identities",
                                     params=dict()))

si_list_result = si_lr_response['result']
hyundai_identities = { si['identifier'] : si for si in si_list_result['identities'] }

print '* Getting language settings'
language_response = call_rogerthat(dict(id=guid(),
                                        method='system.get_languages',
                                        params=dict()))
default_language = language_response['result']['default_language']
all_supported_languages = [default_language] + language_response['result']['supported_languages']

print '* Showing changes'
with open('Hyundai.csv', 'rb') as csvfile:
    r = csv.reader(csvfile, delimiter=',', quotechar='"')

    translated_descriptions = dict()

    first_row = None
    for row in r:
        if not first_row:
            first_row = row
            continue
        d = dict(zip(first_row, row))

        identifier = d['Identity']
        name = d['Name']
        email = d['Identity e-mail']
        phone_number = d['Phonenumber']
        keywords = d['Keywords'].replace(',', '')
        street = d['Adres']
        post_code = d['PC']
        city = d['Gemeente']
        language = d['Taal']
        active = bool(int(d['Actief']))
        new_email = d['Nieuwe identity']

        data = {}
        data['id'] = guid()

        phone_number = phone_number.replace(' ', '').replace(',', '').replace('.', '')

        if active:
            address = "%s\n%s %s" % (street, post_code, city)
            p = {'name':name, 'email':email, 'address':address}
            description = DESCRIPTIONS[default_language] % p
            translated_descriptions[identifier] = dict([(l, DESCRIPTIONS[l] % p) for l in all_supported_languages])

            # TODO: enable recommend, use default homescreen branding, use default phone popup,
            # TODO: use default description branding
            data['method'] = 'system.put_identity'
            data['params'] = {
                'identity': {
                    'identifier': identifier,
                    'name': name,
                    'description': description,
                    'description_use_default': False,
                    'qualified_identifier': new_email,  # TODO: should be qualifiedIdentifier & metadata?
                    'admin_emails': [new_email],
                    'phone_number': phone_number,
                    'phone_number_use_default': False,
                    'search_use_default': False
                }
            }
            if identifier not in hyundai_identities:
                print 'New identity: ', identifier, name

                geo = geocode(address)

                if not DRY_RUN:
                    if geo['status'] == 'OK':
                        lat = geo['lat']
                        lng = geo['lng']

                        data['params']['identity']['search_config'] = {'enabled': True,
                                               'keywords': keywords,
                                               'locations':[{'address': address,
                                                            'lat': lat,
                                                            'lon': lng
                                                            }]
                                               }
                    else:
                        print "Failed to configure search config. Perform it manually."

            elif name.decode('utf-8') != hyundai_identities[identifier]['name']:
                data['params']['identity']['name'] = hyundai_identities[identifier]['name']
            #                print 'Identity renamed: ', identifier, hyundai_identities[identifier]['name'], '-->', name
            elif new_email != hyundai_identities[identifier]['qualified_identifier']:
                print 'Identity email changed: ', identifier, hyundai_identities[identifier]['qualified_identifier'], '-->', new_email
            else:
                # not changed
                continue
        else:
            if identifier in hyundai_identities:
                print 'Identity to remove: ', identifier, name
                resp = call_rogerthat(dict(id=guid(), method="friend.list",
                                           params=dict(service_identity=identifier)))
                result = resp['result']
                for friend in result['friends']:
                    print '    User that will be removed: ', friend['email'], friend['name'], friend['language']
                    if not DRY_RUN:
                        resp = call_rogerthat(dict(id=guid(), method="friend.break_up",
                                                   params=dict(email=friend['email'], service_identity=identifier)))
                        if resp['error']:
                            raise Exception(resp['error'])

                if not DRY_RUN:
                    print '    Removing identity: ', identifier, name
                data['method'] = 'system.delete_identity'
                data['params'] = {'identifier': identifier}
            else:
                # Inactive identity: identifier, name
                continue

        if not DRY_RUN:
            result = call_rogerthat(data)

            if result['error']:
                e = {'identity':identifier, 'error':result['error']}
                logging.error(e)
                raise Exception(str(e))


    if not DRY_RUN:
        # Saving translated descriptions
        print '* Getting translations'
        translation_set = call_rogerthat(dict(id=guid(), method="system.get_translations", params=dict()))['result']
        print '* Updating translations with new descriptions'
        translations = [ dict(type=201,
                              key=td[default_language],
                              values=[ dict(language=l, value=td[l]) for l in td.iterkeys() if l != default_language ])
                        for td in translated_descriptions.itervalues() ]
        translation_set['translations'] += translations

        put_translations_result = call_rogerthat(dict(id=guid(), method="system.put_translations",
                                                      params=dict(translations=translation_set)))
        if put_translations_result['error']:
            raise Exception(put_translations_result['error'])

        print '* Publishing changes'
        publish_changes_result = call_rogerthat(dict(id=guid(), method="system.publish_changes", params=dict()))
        if publish_changes_result['error']:
            raise Exception(publish_changes_result['error'])
