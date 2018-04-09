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
# @@license_version:1.2@@

import logging
from xml.dom import minidom

from google.appengine.api import urlfetch
from google.appengine.ext import webapp, deferred

from rogerthat.bizz.job import run_job
from rogerthat.utils import now
from rogerthat.utils.transactions import run_in_transaction
from solutions.common.cron.news import parse_html_content, transl, \
    create_news_item
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionRssScraperSettings, SolutionRssScraperItem

BROADCAST_TYPE_NEWS = u"News"


class SolutionRssScraper(webapp.RequestHandler):

    def get(self):
        run_job(_qry, [], _worker, [])


def _qry():
    return SolutionRssScraperSettings.query()


def _worker(rss_settings_key):
    rss_settings = rss_settings_key.get()
    if not rss_settings.rss_links:
        return

    service_user = rss_settings.service_user
    service_identity = rss_settings.service_identity
    
    sln_settings = get_solution_settings(service_user)
    if BROADCAST_TYPE_NEWS not in sln_settings.broadcast_types:
        logging.info(sln_settings.broadcast_types)
        logging.error("process_rss_links failed for '%s' no broadcast type found with name '%s'",
                      service_user,
                      BROADCAST_TYPE_NEWS)
        return

    broadcast_type = transl(BROADCAST_TYPE_NEWS, sln_settings.main_language)

    for rss_link in rss_settings.rss_links:
        dry_run = not rss_link.dry_runned
        try:
            response = urlfetch.fetch(rss_link.url, deadline=10)
        except Exception:
            logging.exception("Could not load rss url: %s" % rss_link.url)
            continue
        if response.status_code != 200:
            logging.error("Could not load rss url: %s with status code %s" % (rss_link.url, response.status_code))
            continue

        logging.info('Scraping rss for url %s in dry_run %s', rss_link.url, dry_run)

        doc = minidom.parseString(response.content)
        for item in doc.getElementsByTagName('item'):
            try:
                title = item.getElementsByTagName("title")[0].firstChild.nodeValue
                url = item.getElementsByTagName("link")[0].firstChild.nodeValue
                description_tags = item.getElementsByTagName("description")
                if not description_tags:
                    logging.debug("url: %s", url)
                    logging.info('description not found for %s', item.childNodes)
                    continue
                description_html = description_tags[0].firstChild.nodeValue
                message, _, _ = parse_html_content(description_html)

            except:
                logging.debug("url: %s", url)
                logging.debug(item.childNodes)
                raise

            def trans_send_news():
                db_item_key = SolutionRssScraperItem.create_key(service_user, service_identity, url)
                db_item = db_item_key.get()
                if db_item and not dry_run:
                    return True
                elif not db_item:
                    db_item = SolutionRssScraperItem(key=db_item_key)
                    db_item.timestamp = now()
                    db_item.dry_run = dry_run
                    db_item.put()

                    if not dry_run:
                        deferred.defer(create_news_item, sln_settings, broadcast_type, message, title, url,
                                       _transactional=True)
                return False

            should_break = run_in_transaction(trans_send_news)
            if should_break:
                break

        def trans_update_dry_run():
            db_item = SolutionRssScraperSettings.create_key(service_user, service_identity).get()
            for db_item_rss_link in db_item.rss_links:
                if db_item_rss_link.url != rss_link.url:
                    continue
                db_item_rss_link.dry_runned = True
                db_item.put()
                break

        if dry_run:
            run_in_transaction(trans_update_dry_run)

