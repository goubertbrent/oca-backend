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

import datetime
import logging
import socket

from lxml import html

from google.appengine.api import urlfetch
from google.appengine.api.urlfetch_errors import DeadlineExceededError
from google.appengine.ext import deferred, db
from rogerthat.dal import parent_key
from rogerthat.utils import get_epoch_from_datetime
from solutions.common.bizz import SolutionModule
from solutions.common.dal import get_solution_settings
from solutions.common.models.agenda import Event


def check_for_events(service_user):
    deferred.defer(_process_events, service_user, 1)


def _optional_xpath_text(tree, qry):
    elems = tree.xpath(qry)
    return elems and elems[0].text or u""


def _to_datetime_date(date_str):  # 19/05/2016
    return datetime.date(*map(int, reversed(date_str.split("/"))))


def _date_xrange(start, end):
    delta = datetime.timedelta(days=1)
    current = start
    while current <= end:
        yield current
        current += delta


def _get_event_details(url):
    logging.debug(url)
    try:
        response = urlfetch.fetch(url, deadline=60)
    except socket.timeout:
        logging.exception("_get_event_details failed socket.timeout")
        return
    except DeadlineExceededError:
        logging.exception("_get_event_details failed DeadlineExceededError")
        return
    except:
        logging.exception("_get_event_details failed unkown")
        return

    if response.status_code != 200:
        logging.error("Could not get event details in fr_deuillabarre.\n%s" % response.content)
        return

    tree = html.fromstring(response.content.decode("utf8"))
    end_date_str = start_time_str = end_time_str = u""
    try:
        start_time_str = _optional_xpath_text(tree, '//span[@class="ic-single-starttime"]')  # 09:00
        end_time_str = _optional_xpath_text(tree, '//span[@class="ic-single-endtime"]')  # 19:00
        start_date_str = _optional_xpath_text(tree, '//span[@class="ic-single-startdate"]')  # 19/05/2016
        if not start_date_str:
            start_date_str = tree.xpath('//span[@class="ic-period-startdate"]')[0].text  # 19/05/2016
        end_date_str = _optional_xpath_text(tree, '//span[@class="ic-period-enddate"]')  # 21/05/2016
    except:
        try:
            start_date_str = tree.xpath('//span[@class="ic-single-next"]')[0].text
        except:
            start_date_str = None
            for tmp_start_date_str in tree.xpath('//div[@id="icagenda"]//div[@class="details ic-details"]/text()'):
                if "/" in tmp_start_date_str:
                    start_date_str = tmp_start_date_str
                    break

            if not start_date_str:
                raise Exception("Could not gues start date")

            start_and_end_time_str = _optional_xpath_text(tree, '//div[@id="icagenda"]//div[@class="details ic-details"]/small')
            if start_and_end_time_str:
                splitted_hours = start_and_end_time_str.split(' - ')
                start_time_str = splitted_hours[0]
                end_time_str = splitted_hours[1] if len(splitted_hours) > 1 else ""

    full_description = tree.xpath('//div[@class="ic-full-description"]')
    full_description = full_description[0].text_content() if full_description else u""

    start_date = _to_datetime_date(start_date_str)
    if end_date_str:
        start_dates = list(_date_xrange(start_date, _to_datetime_date(end_date_str)))
    else:
        start_dates = [start_date]

    if start_time_str:
        start_hour_and_minute = map(int, start_time_str.split(':'))
    else:
        start_hour_and_minute = [0, 0]

    if end_time_str:
        end_hour_and_minute = map(int, end_time_str.split(':'))
        end_hour_epoch = 3600 * end_hour_and_minute[0] + end_hour_and_minute[1]
    else:
        end_hour_epoch = 0
    end_hour_epochs = len(start_dates) * [end_hour_epoch]

    start_datetimes = [datetime.datetime(d.year, d.month, d.day, *start_hour_and_minute)
                       for d in start_dates]
    start_epochs = map(get_epoch_from_datetime, start_datetimes)

    return start_epochs, end_hour_epochs, _filter_chars(full_description)


def _filter_chars(txt):
    if not txt:
        return txt
    txt = txt.replace("\r", "")
    txt = txt.replace("\t", "")
    txt = txt.replace("\n", "")
    return txt


def _process_events(service_user, page):
    sln_settings = get_solution_settings(service_user)
    if not sln_settings:
        logging.error("check_for_events_in_fr_deuillabarre failed: sln_settings found for %s", service_user)
        return
    if SolutionModule.AGENDA not in sln_settings.modules:
        logging.error("check_for_events_in_fr_deuillabarre failed: module found for %s", service_user)
        return

    url = u"http://www.mairie-deuillabarre.fr/agenda?page=%s" % page
    response = urlfetch.fetch(url, deadline=60)
    if response.status_code != 200:
        logging.error("Could not check for events in fr_deuillabarre page %s.\n%s", page, response.content,
                      _suppress=False)
        return

    tree = html.fromstring(response.content.decode("utf8"))

    events = tree.xpath('//form[@id="icagenda-list"]//div[@class="event ic-event ic-clearfix"]')
    to_put = []
    for event in events:
        h2_title = event.getchildren()[1].getchildren()[0].getchildren()[0].getchildren()[0]
        div_place = event.getchildren()[1].getchildren()[2]

        title = _filter_chars(h2_title.getchildren()[0].text)
        url = h2_title.getchildren()[0].xpath("@href")[0]
        place = _filter_chars(div_place.text_content() if div_place is not None else u"")
        place = place.replace("Lieu: ", "")

        if not (url.startswith("http://") or url.startswith("https://")):
            url = u"http://www.mairie-deuillabarre.fr%s" % url
        url = unicode(url) if not isinstance(url, unicode) else url
        t = _get_event_details(url)
        if not t:
            continue
        start_epochs, end_hour_epochs, description = t

        event_parent_key = parent_key(service_user, sln_settings.solution)
        event = Event.all().ancestor(event_parent_key).filter("source =", Event.SOURCE_SCRAPER).filter("external_id =", url).get()
        if not event:
            event = Event(parent=event_parent_key,
                          source=Event.SOURCE_SCRAPER,
                          external_id=url)

        event.calendar_id = sln_settings.default_calendar
        event.external_link = url
        event.title = title
        event.description = description
        event.place = place
        event.first_start_date = start_epochs[0]
        event.last_start_date = start_epochs[-1]
        event.start_dates = start_epochs
        event.end_dates = end_hour_epochs
        to_put.append(event)

    if to_put:
        db.put(to_put)

    if events:
        deferred.defer(_process_events, service_user, page + 1)
    else:
        sln_settings.put_identity_pending = True
        sln_settings.put()
