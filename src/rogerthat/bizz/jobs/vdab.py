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

import datetime
import json
import logging
import urllib

import html2text
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google.appengine.ext.deferred import deferred

from mcfw.consts import MISSING
from mcfw.properties import azzert
from rogerthat.bizz.job import run_job
from rogerthat.bizz.jobs.matching import create_job_offer_matches, remove_job_offer_matches
from rogerthat.bizz.jobs.search import re_index_job_offer
from rogerthat.bizz.jobs.vdab_models import VDABJobOffer, VDABAddress
from rogerthat.consts import JOBS_VDAB_QUEUE, JOBS_WORKER_QUEUE, \
    JOBS_CONTROLLER_QUEUE
from rogerthat.models.jobs import VDABSettings, JobOffer, JobOfferInfo, \
    JobOfferFunction, JobOfferEmployer, JobOfferLocation, JobOfferContract, JobOfferSource, JobOfferContactInformation, \
    JobOfferSourceType
from rogerthat.utils import now
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks
from rogerthat.utils.location import coordinates_to_city, address_to_coordinates

API_ENDPOINT = "https://api.vdab.be/services/openservices"
INITIAL_JOBS_SIZE = 200
BULK_JOBS_SIZE = 2000

@ndb.transactional()
def sync_jobs():
    settings = VDABSettings.create_key().get()  # type: VDABSettings
    if not settings:
        return
    from_ = settings.synced_until
    until_ = now()
    if settings.synced_until == 0:
        deferred.defer(_initial_jobs_scheduler, _queue=JOBS_VDAB_QUEUE, _transactional=True)
    else:
        deferred.defer(_bulk_jobs_scheduler, from_, until_, _queue=JOBS_VDAB_QUEUE, _transactional=True)
    settings.synced_until = until_
    settings.put()


def get_contract_type(code):
    contract_type_conversion = {
        'FS': {'key': None, 'label': u'Instapstage'},
        'CM': {'key': None, 'label': u'Collectief maatwerk'},
        'LD': {'key': None, 'label': u'Lokale diensteneconomie'},
        'G': {'key': 'contract_type_001', 'label': u'Gewoon contract'},
        'TW': {'key': None, 'label': u'tewerkstellingsmaatregel'},
        'OW': {'key': None, 'label': u'Occasioneel werk,'},
        'VW': {'key': 'contract_type_007', 'label': u'Vrijwilligerswerk'},
        'AP': {'key': None, 'label': u'Aanwerving met sterke voorkeur voor kandidaten die voldoen aan de voorwaarden voor het bekomen van een werkkaart'},
        'Q': {'key': None, 'label': u'Vervangingscontract brugpensioen - Voorwaarden: uitkeringsgerechtigd werkloos of schoolverlater in wachttijd zijn'},
        'GB': {'key': None, 'label': u'Beperkte tewerkstelling <13 uren/week'},
        'IN': {'key': None, 'label': u'Informatie'},
        'I': {'key': 'contract_type_002', 'label': u'Interimcontract'},
        'IV': {'key': 'contract_type_002', 'label': u'Interim met optie \'vast werk\''},
        'MO': {'key': None, 'label': u'Middenstandsopleiding'},
        'OO': {'key': None, 'label': u'Ondernemingsopleiding'},
        'SB': {'key': None, 'label': u'Jonger zijn dan 26 jaar en ingeschreven zijn als werkzoekende, geen studies met volledig leerplan meer volgen'},
        'WS': {'key': None, 'label': u'Werfreserve'},
        'V': {'key': 'contract_type_003', 'label': u'Studentenjob'},
        'T': {'key': 'contract_type_002', 'label': u'Tijdelijke job'},
        'GC': {'key': 'contract_type_006', 'label': u'Gewoon contract (dienstencheques)'},
        'GA': {'key': None, 'label': u'Vacature uitsluitend voor personen met een arbeidshandicap ingevolge BVR 07-12-2007'},
        'GO': {'key': None, 'label': u'Vlaamse Overheid extra toeleiding kansengroepen'},
        'GD': {'key': 'contract_type_003', 'label': u'Vacature voorbehouden voor deeltijds leerplichtigen'},
        'VU': {'key': 'contract_type_001', 'label': u'Vaste job bij het uitzendkantoor'},
        'Z': {'key': 'contract_type_004', 'label': u'Zelfstandige activiteit'},
        'E': {'key': None, 'label': u'Een aanwervingsexamen'},
        'U': {'key': None, 'label': u'Een aanwervingsexamen selor'},
        '3': {'key': None, 'label': u'Zeelieden (baz - Antwerpen)'},
        'D': {'key': None, 'label': u'Contract Derde Arbeidscircuit'},
        'DJ': {'key': None, 'label': u'Contract Derde Arbeidscircuit - Voorwaarden: minimum 1 jaar uitkeringsgerechtigd werkloos zijn'},
        'F': {'key': None, 'label': u'Vervangingscontract loopbaanonderbreking  privésector - Voorwaarden: o.a. uitkeringsgerechtigd werkloos zijn of schoolverlater. Meer info te bekomen op het nummer 070-34 50 00'},
        'GJ': {'key': 'contract_type_001', 'label': u'gewoon contract, (de werkgever is sterk geïnteresseerd in werkzoekenden  met een JOBKAART)'},
        'H': {'key': None, 'label': u'Jeugdwerkgarantieplan'},
        'J': {'key': 'contract_type_003', 'label': u'Jongerenbanenplan'},
        'K': {'key': None, 'label': u'Werkervaringsplan'},
        'L': {'key': 'contract_type_002', 'label': u'Vervangingscontract loopbaanonderbreking openbare sector - Voorwaarden: o.a. uitkeringsgerechtigd werkloos zijn. Meer info te bekomen op het nr. 070-34 50 00'},
        'M': {'key': None, 'label': u'Voordeelbaan - Voorwaarden: in bezit zijn van een banenkaart, te bekomen bij de RVA'},
        'MI': {'key': None, 'label': u'MINA-contract - Voorwaarden: ocmw-uitkering genieten of minimum 2 jaar werkloos zijn'},
        'O': {'key': None, 'label': u'Gesco-contract'},
        'PC': {'key': None, 'label': u'WEP+vacature, voorbehouden voor langdurig werkzoekenden (inlichtingen bij je consulent of de VDAB-servicelijn)'},
        'S': {'key': None, 'label': u'Stage'},
        'W': {'key': 'contract_type_003', 'label': u'Eerste werkervaringscontract'},
        'WE': {'key': 'contract_type_002', 'label': u'Werkervaringsplan'},
        'X': {'key': None, 'label': u'Extra (horeca)'},
        'Y': {'key': 'contract_type_003', 'label': u'Ingroeibaan'},
        'B': {'key': None, 'label': u'Dienstenbaan - Voorwaarden: minimum 2 jaar uitkeringsgerechtigd werkloos zijn. vanaf 45 jaar is 6 maanden uitkeringsgerechtigd werkloos zijn voldoende'},
        'AM': {'key': None, 'label': u'Arbeidszorg Meerbanenplan - voorwaarden: verplicht ingeschreven werkzoekende + opgenomen zijn in de doelgroep arbeidszorg na een activeringsscreening of -begeleiding met als advies arbeidszorg (werkgever moet attest hiervan opvragen bij VDAB)'},
        'AZ': {'key': None, 'label': u'Arbeidszorg (oude plaatsen) - voorwaarden: ingeschreven zijn als werkzoekende bij de VDAB +  opgenomen zijn in de doelgroep arbeidszorg door de VDAB op advies van ATB (attest hiervan is af te leveren door de VDAB op vraag van de werkgever)'},
        'GS': {'key': 'contract_type_001', 'label': u'Gewoon contract, voorbehouden voor werkzoekenden, ouder dan 18 jaar, met een gekwalificeerde beroepsopleiding of een vergelijkbare beroepservaring'},
        'IB': {'key': None, 'label': u'Contract voor invoegbedrijf - Inlichtingen bij je consulent'},
        'KB': {'key': None, 'label': u'Gewoon contract, voorbehouden voor werkzoekenden die in aanmerking komen voor SINE. Inlichtingen bij je consulent'},
        'KG': {'key': None, 'label': u'Gewoon contract, voorbehouden voor werkzoekenden die in aanmerking komen voor SINE. Inlichtingen bij je consulent'},
        'BEVORD': {'key': None, 'label': u'Bevorderingen'},
        'HORIZMOB': {'key': None, 'label': u'Horizontale mobiliteit'},
        'EXTMOB': {'key': None, 'label': u'Externe mobiliteit'},
        'GRDVER': {'key': None, 'label': u'Graadverandering'},
        'HERPL': {'key': None, 'label': u'Herplaatsing'},
        'STAT': {'key': None, 'label': u'Statutair'},
        'CONTRACTONB': {'key': 'contract_type_001', 'label': u'Contractueel onbepaalde duur'},
        'CONTRACTBEP': {'key': 'contract_type_002', 'label': u'Contractueel bepaalde duur'},
        'STUDJOB': {'key': 'contract_type_003', 'label': u'Studentenjobs'},
        'LP': {'key': 'contract_type_003', 'label': u'Leerplek'},
        'STARTB': {'key': 'contract_type_003', 'label': u'Startbanen / leerovereenkomsten'},
        'STAGES': {'key': None, 'label': u'Stages'},
        'MGMTJOB': {'key': 'contract_type_001', 'label': u'Managementjobs'},
        'PMABJOB': {'key': None, 'label': u'Voorbehouden betrekking voor personen met een arbeidshandicap'},
        'TV': {'key': 'contract_type_002', 'label': u'Tijdelijke job (met optie vast)'},
        'FL': {'key': 'contract_type_005', 'label': u'Een flexijob is een bijverdienste en staat open voor iedereen die, reeds 3 kwartalen geleden, minstens 4/5 bij een andere werkgever, uit een andere sector, in vast dienstverband werkt'},
        'AL': {'key': 'contract_type_001', 'label': u'Activa langdurig werkzoekenden'},
    }

    azzert(code in contract_type_conversion, "Contract type conversion not found for %s" % (code))

    return contract_type_conversion[code]


def get_job_domain(code):
    job_domain_conversion = {'JOBCAT01':'job_domain_001',  # Aankoop
                             'JOBCAT02':'job_domain_002',  # Administratie
                             'JOBCAT03':'job_domain_003',  # Bouw
                             'JOBCAT04':'job_domain_004',  # Communicatie
                             'JOBCAT05':'job_domain_005',  # Creatief
                             'JOBCAT06':'job_domain_006',  # Financieel
                             'JOBCAT07':'job_domain_007',  # Gezondheid
                             'JOBCAT08':'job_domain_008',  # Horeca en toerisme
                             'JOBCAT09':'job_domain_009',  # Human resources
                             'JOBCAT10':'job_domain_010',  # ICT
                             'JOBCAT11':'job_domain_011',  # Juridisch
                             'JOBCAT12':'job_domain_012',  # Land- en tuinbouw
                             'JOBCAT13':'job_domain_013',  # Logistiek en transport
                             'JOBCAT14':'job_domain_014',  # Dienstverlening
                             'JOBCAT15':'job_domain_015',  # Management
                             'JOBCAT16':'job_domain_016',  # Marketing
                             'JOBCAT17':'job_domain_017',  # Onderhoud
                             'JOBCAT18':'job_domain_018',  # Onderwijs
                             'JOBCAT19':'job_domain_019',  # Overheid
                             'JOBCAT20':'job_domain_020',  # Onderzoek en ontwikkeling
                             'JOBCAT21':'job_domain_021',  # Productie
                             'JOBCAT22':'job_domain_022',  # Techniek
                             'JOBCAT23':'job_domain_023',  # Verkoop
                             'JOBCAT24':'job_domain_024',  # Andere
                             }

    azzert(code in job_domain_conversion, "Job domain conversion not found for %s" % (code))

    return job_domain_conversion[code]


def get_application_preference(code):
    contract_type_conversion = {
        'E': u'E-mail',
        'T': u'Telefoon',
        'Z': u'Brief',
        'S': u'Brief en CV',
        'P': u'Persoonlijk aanmelden',
        'V': u'Vrij te kiezen'
    }

    azzert(code in contract_type_conversion, "Application preference conversion not found for %s" % (code))

    return contract_type_conversion[code]


def get_geo_point_from_address(address_to):
    # type: (VDABAddress) -> ndb.GeoPt
    if not (address_to.postcode or address_to.gemeente or address_to.straat):
        return None

    address_str = u'Belgie'
    if address_to.postcode:
        address_str += u' %s' % address_to.postcode
    if address_to.gemeente:
        address_str += u' %s' % address_to.gemeente
    if address_to.straat:
        address_str += u' %s' % address_to.straat
    try:
        lat, lon, _, _, _ = address_to_coordinates(address_str, postal_code_required=False)
        return ndb.GeoPt(lat, lon)
    except:
        logging.warn(u'Failed to address for %s', address_str)

    if address_to.gemeente:
        address_str = u'Belgie %s' % address_to.gemeente
        try:
            lat, lon, _, _, _ = address_to_coordinates(address_str, postal_code_required=False)
            return ndb.GeoPt(lat, lon)
        except:
            logging.warn(u'Failed to address for %s', address_str)

    if address_to.postcode:
        address_str = u'Belgie %s' % address_to.postcode
        try:
            lat, lon, _, _, _ = address_to_coordinates(address_str, postal_code_required=False)
            return ndb.GeoPt(lat, lon)
        except:
            logging.warn(u'Failed to address for %s', address_str)

    return None


def _do_request(path, params=None):
    settings = VDABSettings.create_key().get()
    if not settings:
        return None
    headers = {
        "X-IBM-Client-Id": settings.client_id,
        "Accept": "application/json"
    }
    request_params = urllib.urlencode(params or dict())
    url = u"%s/%s?%s" % (API_ENDPOINT, path, request_params)
    logging.info("Sending request to %s", url)
    response = urlfetch.fetch(url, headers=headers, deadline=60)
    azzert(response.status_code == 200,
           "Got response status code %s and response content: %s" % (response.status_code, response.content))
    # logging.info("Got response: %s" % response.content)
    return json.loads(response.content)


def _get_initial_jobs_result(offset=0):
    params = dict(velden="status",
                  vanaf=offset,
                  aantal=INITIAL_JOBS_SIZE)
    return _do_request(u'v2/vacatures', params)


def _run_initial_jobs_tasks(results):
    tasks = [create_task(_update_job, result['vacatureReferentie']['interneReferentie'], result['status'], False)
             for result in results.get('resultaten', [])]
    logging.debug('_run_initial_jobs_tasks.tasks: %s', len(tasks))
    schedule_tasks(tasks, JOBS_WORKER_QUEUE)


def _initial_jobs_updater(offset):
    results = _get_initial_jobs_result(offset)
    _run_initial_jobs_tasks(results)


def _initial_jobs_scheduler():
    results = _get_initial_jobs_result(0)
    tasks = []
    amount = results.get('aantal', 0)
    next_offset = INITIAL_JOBS_SIZE
    while True:
        if amount <= next_offset:
            break
        tasks.append(create_task(_initial_jobs_updater, next_offset))
        next_offset += INITIAL_JOBS_SIZE

    schedule_tasks(tasks, JOBS_VDAB_QUEUE)
    _run_initial_jobs_tasks(results)


def _get_bulk_jobs_result(from_, until_, offset=0):
    from_date_str = datetime.datetime.fromtimestamp(from_).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    until_date_str = datetime.datetime.fromtimestamp(until_).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    params = dict(van=from_date_str,
                  tot=until_date_str,
                  vanaf=offset,
                  aantal=BULK_JOBS_SIZE)
    return _do_request(u'v2/vacatures/bulk', params)


def _run_bulk_jobs_tasks(results):
    tasks = [create_task(_update_job, result['vacatureReferentie']['interneReferentie'], result['status'], True)
             for result in results.get('resultaten', [])]
    logging.debug('_run_bulk_jobs_tasks.tasks: %s', len(tasks))
    schedule_tasks(tasks, JOBS_WORKER_QUEUE)


def _bulk_jobs_updater(from_, until_, offset):
    results = _get_bulk_jobs_result(from_, until_, offset)
    _run_bulk_jobs_tasks(results)


def _bulk_jobs_scheduler(from_, until_):
    results = _get_bulk_jobs_result(from_, until_, 0)
    tasks = []
    amount = results.get('aantal', 0)
    next_offset = BULK_JOBS_SIZE
    while True:
        if amount <= next_offset:
            break
        tasks.append(create_task(_bulk_jobs_updater, from_, until_, next_offset))
        next_offset += BULK_JOBS_SIZE

    logging.debug('_bulk_jobs_scheduler.amount: %s', amount)
    logging.debug('_bulk_jobs_scheduler.tasks: %s', len(tasks))
    run_tasks = True
    if amount > 100000:
        logging.debug('_bulk_jobs_scheduler.amount>100k')
    if amount > 50000:
        logging.debug('_bulk_jobs_scheduler.amount>50k')
        run_tasks = False
    if amount > 10000:
        logging.debug('_bulk_jobs_scheduler.amount>10k')
    if amount > 5000:
        logging.debug('_bulk_jobs_scheduler.amount>5k')

    if run_tasks:
        schedule_tasks(tasks, JOBS_VDAB_QUEUE)
        _run_bulk_jobs_tasks(results)
    else:
        logging.warn('Ignoring tasks') # todo remove when VDAB fixed their end


def _update_job(source_id, status, should_create_matches=False):
    if 'NOT_FOUND' in source_id:
        return
    job_offer = JobOffer.get_by_source(JobOfferSourceType.VDAB, source_id)
    if not job_offer:
        if status not in ('GEPUBLICEERD',):
            return
    deferred.defer(_update_job_limited, source_id, should_create_matches, _queue=JOBS_VDAB_QUEUE)


def _update_job_limited(source_id, should_create_matches=False):
    job_offer = JobOffer.get_by_source(JobOfferSourceType.VDAB, source_id)
    new_job = False
    skip_job = False
    if not job_offer:
        new_job = True
        job_offer = JobOffer()
        source = JobOfferSource()
        source.type = JobOfferSourceType.VDAB
        source.id = source_id
        source.name = 'VDAB'
        source.avatar_url = 'https://storage.googleapis.com/oca-files/jobs/VDAB.jpg'
        job_offer.source = source

    try:
        job_offer.data = _do_request(u'v2/vacatures/%s' % source_id)
    except AssertionError as ae:
        logging.warn(ae)
        if 'Invalid string syntax' in ae.message:
            pass
        elif 'is geen bestaande vacature' in ae.message:
            pass
        else:
            raise
        skip_job = True

    if skip_job:
        if not new_job:
            job_offer.visible = False
            job_offer.invisible_reason = JobOffer.INVISIBLE_REASON_SKIP
            job_offer.put()

            re_index_job_offer(job_offer)
            remove_job_offer_matches(job_offer.id)
        return

    _save_job_offer(job_offer, new_job=new_job, should_create_matches=should_create_matches)


def _save_job_offer(job_offer, new_job=False, should_create_matches=False):
    # type: (JobOffer, bool, bool) -> None
    job_detail = VDABJobOffer.from_dict(job_offer.data)
    address = MISSING.default(job_detail.tewerkstellingsadres, None)
    if job_offer.data['status'] in ('GEPUBLICEERD',):
        job_offer.visible = True
        job_offer.invisible_reason = None
        
    dubbels = job_offer.data.get('dubbels')
    is_dubble = False
    if dubbels:
        parentUuid = dubbels.get('parentUuid')
        if parentUuid and parentUuid != job_offer.source.id:
            is_dubble = True

    if job_offer.data['status'] not in ('GEPUBLICEERD',):
        job_offer.visible = False
        job_offer.invisible_reason = JobOffer.INVISIBLE_REASON_STATUS
    elif is_dubble:
        job_offer.visible = False
        job_offer.invisible_reason = JobOffer.INVISIBLE_REASON_DUBBLE
    elif not address:
        job_offer.visible = False
        job_offer.invisible_reason = JobOffer.INVISIBLE_REASON_LOCATION_MISSING
    elif address.landCode and address.landCode != u'BE':
        job_offer.visible = False
        job_offer.invisible_reason = JobOffer.INVISIBLE_REASON_LOCATION_COUNTRY
    else:
        address_locatie = MISSING.default(address.locatie, None)
        if address_locatie:
            geo_location = ndb.GeoPt(address_locatie.latitude,
                                     address_locatie.longitude)
        else:
            geo_location = get_geo_point_from_address(address)

        if geo_location:
            if address.gemeente:
                city = address.gemeente.strip()
            else:
                try:
                    city = coordinates_to_city(geo_location.lat,
                                               geo_location.lon)
                except:
                    logging.warn(u'Failed to execute coordinates_to_city for %s', address)
                    job_offer.visible = False
                    job_offer.invisible_reason = JobOffer.INVISIBLE_REASON_LOCATION_LATLON
        else:
            job_offer.visible = False
            job_offer.invisible_reason = JobOffer.INVISIBLE_REASON_LOCATION_UNKNOWN

    if job_offer.visible:
        description = job_offer.data['functie'].get('omschrijving')
        if not description:
            description = job_offer.data['arbeidsovereenkomst'].get('extra')
        if not description:
            job_offer.visible = False
            job_offer.invisible_reason = JobOffer.INVISIBLE_REASON_DESCRIPTION

    if not job_offer.visible:
        job_offer.put()
        re_index_job_offer(job_offer)
        if not new_job:
            remove_job_offer_matches(job_offer.id)
        return

    job_offer.info = JobOfferInfo()

    job_offer.info.function = JobOfferFunction()
    job_offer.info.function.title = job_offer.data['functie']['functieTitel']
    job_offer.info.function.description = html2text.html2text(description) if description else None

    job_offer.info.employer = JobOfferEmployer()
    job_offer.info.employer.name = job_offer.data.get('leverancier', {}).get('naam')
    if job_offer.info.employer.name:
        job_offer.info.employer.name = job_offer.info.employer.name.strip()
    
    job_offer.info.location = JobOfferLocation()
    job_offer.info.location.geo_location = geo_location
    job_offer.info.location.city = city

    contract_type = get_contract_type(job_offer.data['arbeidsovereenkomst']['arbeidsContract'])
    job_offer.info.contract = JobOfferContract()
    job_offer.info.contract.type = contract_type['key']

    if job_offer.info.employer.name:
        if job_offer.data.get('sollicitatieprocedure', {}).get('sollicitatieAdres', {}).get('gemeente'):
            jobDescriptionTitle = u'**%s** in **%s** zoekt\n' % (job_offer.info.employer.name, job_offer.data['sollicitatieprocedure']['sollicitatieAdres']['gemeente'])
        else:
            jobDescriptionTitle = u'**%s** zoekt\n' % (job_offer.info.employer.name)
    else:
        jobDescriptionTitle = u''

    applicationDetails = u''
    if job_offer.data.get('vrijeVereiste'):
        applicationDetails += u'## Profiel\n'
        applicationDetails += u'%s\n' % html2text.html2text(job_offer.data['vrijeVereiste'])
    if job_offer.data['arbeidsovereenkomst'].get('extra'):
        applicationDetails += u'## Aanbod\n'
        applicationDetails += u'%s\n' % html2text.html2text(job_offer.data['arbeidsovereenkomst']['extra'])

    applicationDetails += u'## Plaats tewerkstelling\n'
    city = address.gemeente
    zipcode = address.postcode
    if city and zipcode:
        applicationDetails += u'%s %s\n' % (zipcode, city)
    elif city:
        applicationDetails += u'%s\n' % (city)
    else:
        applicationDetails += u'%s\n' % job_offer.info.location.city

    applicationDetails += u'## Waar en hoe solliciteren?\n'
    applicationCV = job_offer.data['sollicitatieprocedure'].get('cvGewenst')
    applicationMotivationLetter = job_offer.data['sollicitatieprocedure'].get('motivatiebriefGewenst')
    applicationContact = job_offer.data['sollicitatieprocedure'].get('contactpersoon', {}).get('naam')
    applicationPreferencesWebsite = job_offer.data['sollicitatieprocedure'].get('sollicitatieVia', {}).get('webformulier')
    applicationPreferencesEmail = job_offer.data['sollicitatieprocedure'].get('sollicitatieVia', {}).get('email')
    applicationPreferencesPhone = job_offer.data['sollicitatieprocedure'].get('sollicitatieVia', {}).get('telefoon')
    applicationPreferencesLetter = job_offer.data['sollicitatieprocedure'].get('sollicitatieVia', {}).get('brief')
    applicationPreferencesPersonal = job_offer.data['sollicitatieprocedure'].get('sollicitatieVia', {}).get('persoonlijkAanmelden')
    applicationPreferencesExtra = job_offer.data['sollicitatieprocedure'].get('sollicitatieVia', {}).get('extraInfoProcedure')
    applicationDescription = job_offer.data['sollicitatieprocedure'].get('omschrijving')

    job_offer.info.contact_information = JobOfferContactInformation()

    if applicationCV is not None:
        applicationDetails += u'**CV Gewenst**: %s\n' % (u'Ja' if applicationCV else u'Nee')
    if applicationMotivationLetter is not None:
        applicationDetails += u'**Motivatiebrief Gewenst**: %s\n' % (u'Ja' if applicationMotivationLetter else u'Nee')
    if applicationPreferencesPersonal is not None:
        applicationDetails += u'**Persoonlijk aanmelden**: %s\n' % (u'Ja' if applicationPreferencesPersonal else u'Nee')

    if applicationContact:
        applicationDetails += u'**Contact**: %s\n' % applicationContact
    if applicationPreferencesPhone:
        job_offer.info.contact_information.phone_number = applicationPreferencesPhone
        applicationDetails += u'**Per telefoon**: [%s](tel://%s)\n' % (applicationPreferencesPhone, applicationPreferencesPhone)
    if applicationPreferencesEmail:
        job_offer.info.contact_information.email = applicationPreferencesEmail
        applicationDetails += u'**Per email**: [%s](mailto://%s)\n' % (applicationPreferencesEmail, applicationPreferencesEmail)
    if applicationPreferencesLetter:
        applicationDetails += u'**Per brief**: %s\n' % applicationPreferencesLetter
    if applicationPreferencesWebsite:
        job_offer.info.contact_information.website = applicationPreferencesWebsite
        applicationDetails += u'\n[Soliciteer nu](%s)' % applicationPreferencesWebsite

    if applicationDescription:
        applicationDetails += u'\n%s' % html2text.html2text(applicationDescription)
    if applicationPreferencesExtra:
        if not applicationDescription or applicationDescription != applicationPreferencesExtra:
            applicationDetails += u'\n%s' % html2text.html2text(applicationPreferencesExtra)

    job_offer.info.details = u"""%s## %s
%s
## Functieomschrijving
%s
%s
""" % (jobDescriptionTitle,
       job_offer.info.function.title,
       contract_type['label'],
       job_offer.info.function.description,
       applicationDetails)

    job_offer.info.details = job_offer.info.details.replace(u'\u0095', u'\n*')

    job_offer.job_domains = [get_job_domain(jd) for jd in job_offer.data['functie'].get('jobdomeinen', [])]

    job_offer.put()

    re_index_job_offer(job_offer)

    if should_create_matches:
        create_job_offer_matches(job_offer)


def save_all_job_offers():
    run_job(_get_all_job_offers, [], _save_all_job_offers, [],
            controller_queue=JOBS_CONTROLLER_QUEUE,
            worker_queue=JOBS_WORKER_QUEUE)


def _get_all_job_offers():
    return JobOffer.query().filter(JobOffer.source.type == JobOfferSourceType.VDAB).filter(JobOffer.visible == True)


def _save_all_job_offers(key):
    _save_job_offer(key.get())
