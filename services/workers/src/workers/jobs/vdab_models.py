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

from common.mcfw.properties import unicode_property, typed_property, float_property, bool_property, unicode_list_property, \
    long_property, long_list_property
from common.to import TO


class VDABProfile(TO):
    code = unicode_property('code')
    ervaring = unicode_property('ervaring')


class VDABFunction(TO):
    beroepsprofiel = typed_property('beroepsprofiel', VDABProfile, default=None)  # type: VDABProfile
    functieTitel = unicode_property('functieTitel')
    omschrijving = unicode_property('omschrijving')
    jobdomeinen = unicode_list_property('jobdomeinen')


class VDABLocation(TO):
    latitude = float_property('latitude')
    longitude = float_property('longitude')


class VDABAddress(TO):
    busnummer = unicode_property('busnummer')
    gemeente = unicode_property('gemeente')
    huisnummer = unicode_property('huisnummer')
    landCode = unicode_property('landCode')
    locatie = typed_property('locatie', VDABLocation, default=None)  # type: VDABLocation
    postcode = unicode_property('postcode')
    regioCode = unicode_property('regioCode')
    straat = unicode_property('straat')


class VDABContactPerson(TO):
    naam = unicode_property('naam')
    aanspreking = unicode_property('aanspreking')
    functie = unicode_property('functie')
    telefoonNummer = unicode_property('telefoonNummer')
    fax = unicode_property('fax')
    email = unicode_property('email')


class VDABApplyVia(TO):
    webformulier = unicode_property('webformulier')
    email = unicode_property('email')
    telefoon = unicode_property('telefoon')
    fax = unicode_property('fax')
    brief = bool_property('brief')
    persoonlijkAanmelden = bool_property('persoonlijkAanmelden')
    extraInfoProcedure = unicode_property('extraInfoProcedure')


class VDABApplyProcedure(TO):
    cvGewenst = bool_property('cvGewenst')
    motivatiebriefGewenst = bool_property('motivatiebriefGewenst')
    omschrijving = unicode_property('omschrijving')
    sollicitatieAdres = typed_property('sollicitatieAdres', VDABAddress, default=None)  # type: VDABAddress
    contactpersoon = typed_property('contactpersoon', VDABContactPerson, default=None)  # type: VDABContactPerson
    sollicitatieVia = typed_property('sollicitatieVia', VDABApplyVia, default=None)  # type: VDABApplyVia


class VDABVacatureReference(TO):
    externeReferentie = unicode_property('externeReferentie')
    interneReferentie = unicode_property('interneReferentie')


class VDABIrmAssistance(TO):
    irmRegioCodes = unicode_list_property('irmRegioCodes')


class VDABAssistance(TO):
    irmAssistentie = typed_property('irmAssistentie', VDABIrmAssistance, default=None)


class VDABLaborContract(TO):
    aantalDagen = long_property('aantalDagen')
    aantalUur = long_property('aantalUur')
    arbeidsContract = unicode_property('arbeidsContract')
    arbeidsContractDuur = unicode_property('arbeidsContractDuur')
    arbeidsRegime = unicode_property('arbeidsRegime')
    arbeidsStelsel = unicode_list_property('arbeidsStelsel')
    extra = unicode_property('extra')
    maximumBrutoLoon = float_property('maximumBrutoLoon')
    minimumBrutoLoon = float_property('minimumBrutoLoon')
    vermoedelijkeStartdatum = unicode_property('vermoedelijkeStartdatum')

class VDABSupplier(TO):
    naam = unicode_property('naam')
    kboNummer = unicode_property('kboNummer')
    prioriteit = long_property('prioriteit')


class VDABDoubles(TO):
    parentUuid = unicode_property('parentUuid')
    dubbelIds = long_list_property('dubbelIds')


class VDABJobOffer(TO):
    aantalJobs = long_property('aantalJobs')
    arbeidsovereenkomst = typed_property('arbeidsovereenkomst', VDABLaborContract, default=None)  # type: VDABLaborContract
    bron = unicode_property('bron')
    depublicatieDatum = unicode_property('depublicatieDatum')
    functie = typed_property('functie', VDABFunction, default=None)  # type: VDABFunction
    leverancier = typed_property('leverancier', VDABSupplier, default=None)  # type: VDABSupplier
    profiel = typed_property('profiel', VDABProfile, default=None)  # type: VDABProfile
    publicatieDatum = unicode_property('publicatieDatum')
    sollicitatieprocedure = typed_property('sollicitatieprocedure', VDABApplyProcedure, default=None)  # type: VDABApplyProcedure
    startDatum = unicode_property('startDatum')
    status = unicode_property('status')  # GEPUBLICEERD,NIET_GEPUBLICEERD, AFGESLOTEN
    tewerkstellingsadres = typed_property('tewerkstellingsadres', VDABAddress, default=None)  # type: VDABAddress
    vacatureReferentie = typed_property('vacatureReferentie', VDABVacatureReference, default=None)  # type: VDABVacatureReference
    versie = long_property('versie')
    vrijeVereiste = unicode_property('vrijeVereiste')
    assistentie = typed_property('assistentie', VDABAssistance, default=None)  # type: VDABAssistance
    dubbels = typed_property('dubbels', VDABDoubles, default=None)  # type: VDABDoubles
    internationaalOpengesteld = bool_property('internationaalOpengesteld')
    vacatureType = unicode_property('vacatureType')  # SJABLOON, ONDERWIJS, VLAAMSE_OVERHEID_EXTERN
