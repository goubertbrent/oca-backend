# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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
# @@license_version:1.5@@

from datetime import datetime
import logging
import rfc822
from urlparse import urlparse
from xml.dom import minidom

from bs4 import BeautifulSoup
import dateutil.parser
from dateutil.relativedelta import relativedelta
from google.appengine.api import urlfetch
from google.appengine.ext import webapp, ndb

from rogerthat.bizz.job import run_job
from rogerthat.consts import HIGH_LOAD_WORKER_QUEUE
from rogerthat.models.news import NewsGroup
from rogerthat.to.push import remove_html
from rogerthat.utils import now, get_epoch_from_datetime
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks
from solutions.common.cron.news import html_unescape, html_to_markdown, transl, \
    create_news_item, update_news_item, news_item_hash, delete_news_item
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionRssScraperSettings, SolutionRssScraperItem


BROADCAST_TYPE_NEWS = u"News"
BROADCAST_TYPE_EVENTS = u"Events"
BROADCAST_TYPE_TRAFIC = u"Trafic"
BROADCAST_TYPE_TRAFFIC = u"Traffic"
BROADCAST_TYPE_PRESS = u"Press"


class SolutionRssScraper(webapp.RequestHandler):

    def get(self):
        run_job(_qry, [], _worker, [])


def _qry():
    return SolutionRssScraperSettings.query()


def _worker(rss_settings_key):
    rss_settings = rss_settings_key.get()  # type: SolutionRssScraperSettings
    if not rss_settings.rss_links:
        return
    service_user = rss_settings.service_user
    service_identity = rss_settings.service_identity
    sln_settings = get_solution_settings(service_user)

    must_update_settings = False
    scraped_items = []
    tasks = []
    to_put = []
    oldest_dates = {}
    can_delete = True

    new_news_item_ids = []
    last_week_datetime = datetime.now() - relativedelta(days=7)

    for rss_link in rss_settings.rss_links:
        app_ids = rss_link.app_ids if rss_link.app_ids else None
        feed_name = None
        broadcast_type_key = BROADCAST_TYPE_NEWS
        if rss_link.group_type and rss_link.group_type == NewsGroup.TYPE_EVENTS:
            broadcast_type_key = BROADCAST_TYPE_EVENTS
        elif rss_link.group_type and rss_link.group_type == NewsGroup.TYPE_TRAFFIC:
            if BROADCAST_TYPE_TRAFIC in sln_settings.broadcast_types:
                broadcast_type_key = BROADCAST_TYPE_TRAFIC
            else:
                broadcast_type_key = BROADCAST_TYPE_TRAFFIC
        elif rss_link.group_type and rss_link.group_type == NewsGroup.TYPE_PRESS:
            broadcast_type_key = BROADCAST_TYPE_PRESS
            feed_name = u'press'

        if broadcast_type_key not in sln_settings.broadcast_types:
            logging.info(sln_settings.broadcast_types)
            logging.error("process_rss_links failed for '%s' and url '%s' no broadcast type found with name '%s'",
                          service_user,
                          rss_link.url,
                          broadcast_type_key)
            can_delete = False
            continue

        broadcast_type = transl(broadcast_type_key, sln_settings.main_language)

        dry_run = not rss_link.dry_runned
        if dry_run:
            must_update_settings = True
        try:
            response = urlfetch.fetch(rss_link.url, deadline=10)  # type: urlfetch._URLFetchResult
        except Exception:
            logging.exception("Could not load rss url: %s" % rss_link.url)
            can_delete = False
            continue
        if response.status_code != 200:
            can_delete = False
            logging.error("Could not load rss url: %s with status code %s" % (rss_link.url, response.status_code))
            continue

        logging.info('Scraping rss for url %s in dry_run %s', rss_link.url, dry_run)

        items, keys = _parse_items(response.content, service_identity, service_user, rss_link.url)
        scraped_items.extend(items)
        if items:
            oldest_dates[rss_link.url] = sorted([s for s in items], key=lambda x: x.date)[0].date
        else:
            oldest_dates[rss_link.url] = None

        saved_items = {item.key.id(): item for item in ndb.get_multi(keys) if
                       item}  # type: dict[str, SolutionRssScraperItem]

        for scraped_item in items:
            # Backwards compat - in the past only url was used as key
            item = saved_items.get(scraped_item.guid) or saved_items.get(scraped_item.url)
            if scraped_item.id in new_news_item_ids:
                continue
            if item:
                if not item.dry_run and item.news_id and scraped_item.hash != item.hash:
                    logging.debug('update_news_item guid:%s url:%s', scraped_item.guid, scraped_item.url)
                    new_news_item_ids.append(scraped_item.id)
                    tasks.append(create_task(update_news_item, item.news_id, sln_settings, broadcast_type,
                                             scraped_item.message, scraped_item.title, scraped_item.url,
                                             scraped_item.image_url))
                    item.hash = scraped_item.hash
                    to_put.append(item)
            else:
                new_key = SolutionRssScraperItem.create_key(service_user, service_identity, scraped_item.id)
                new_item = SolutionRssScraperItem(key=new_key,
                                                  timestamp=now(),
                                                  dry_run=dry_run,
                                                  hash=scraped_item.hash,
                                                  date=scraped_item.date,
                                                  rss_url=scraped_item.rss_url)

                if not dry_run:
                    if scraped_item.date and scraped_item.date < last_week_datetime:
                        logging.debug('new_outdated_news_item guid:%s url:%s', scraped_item.guid, scraped_item.url)
                    else:
                        new_news_item_ids.append(scraped_item.id)
                        logging.debug('create_news_item guid:%s url:%s', scraped_item.guid, scraped_item.url)
                        tasks.append(create_task(create_news_item, sln_settings, broadcast_type, scraped_item.message,
                                                 scraped_item.title, scraped_item.url, rss_settings.notify,
                                                 scraped_item.image_url, new_key, app_ids=app_ids, feed_name=feed_name))
                to_put.append(new_item)

    scraped_items = sorted([s for s in scraped_items if s.date], key=lambda x: x.date)  # oldest items first
    # Don't check if we need to delete items in case one of the rss urls didn't work
    if can_delete:
        to_delete, delete_tasks = get_deleted_rss_items(oldest_dates, scraped_items, service_identity, service_user)
        tasks.extend(delete_tasks)
    else:
        to_delete = []

    def trans():
        if must_update_settings:
            settings = SolutionRssScraperSettings.create_key(service_user, service_identity).get()
            for link in settings.rss_links:
                link.dry_runned = True
            settings.put()

        if to_put:
            logging.info('Saving %s SolutionRssScraperItem', len(to_put))
            ndb.put_multi(to_put)
        if to_delete:
            logging.info('Deleting %s SolutionRssScraperItem', len(to_delete))
            ndb.delete_multi(to_delete)

    if must_update_settings or to_delete or to_put:
        ndb.transaction(trans, xg=True)
    if tasks:
        logging.info('Scheduling %d tasks to create/update/delete news items', len(tasks))
        schedule_tasks(tasks, HIGH_LOAD_WORKER_QUEUE)


def get_deleted_rss_items(oldest_dates, scraped_items, service_identity, service_user):
    to_delete = []
    tasks = []
    if not scraped_items:
        return [], []
    oldest_item_date = scraped_items[0].date
    if not scraped_items or not oldest_item_date:
        return [], []
    previous_items = {i.key.id(): i for i in SolutionRssScraperItem.list_after_date(service_user, service_identity,
                                                                                    oldest_item_date)}
    # Find deleted items in rss feed, if any
    found_ids = set()
    for previous_id in previous_items:
        url = previous_items[previous_id].rss_url
        if not url:
            found_ids.add(previous_id)
            continue
        if url not in oldest_dates:
            # Scraper url was removed, don't delete these items
            found_ids.add(previous_id)
            continue
        oldest = oldest_dates[url]
        if not oldest:
            found_ids.add(previous_id)
            continue
        for scraped_item in scraped_items:
            if scraped_item.date and oldest <= scraped_item.date:
                if scraped_item.guid == previous_id or scraped_item.url == previous_id:
                    found_ids.add(previous_id)
    missing_ids = set(previous_items.keys()).difference(found_ids)
    if missing_ids:
        logging.info('Will delete news items: %s - %s', missing_ids, [previous_items[i].news_id for i in missing_ids])
    for missing_id in missing_ids:
        missing_item = previous_items[missing_id]
        to_delete.append(missing_item.key)
        if missing_item.news_id:
            tasks.append(create_task(delete_news_item, missing_item.news_id, service_user))
    return to_delete, tasks


class ScrapedItem(object):

    def __init__(self, title, url, guid, message, date, rss_url, image_url):
        self.title = title
        self.url = url
        self.guid = guid
        self.id = guid or url
        self.message = message
        self.date = date
        self.rss_url = rss_url
        self.image_url = image_url
        self.hash = news_item_hash(title, message, image_url)


def _parse_items(xml_content, service_identity, service_user, rss_url):
    # type: (str, str, users.User, str) -> ([ScrapedItem], [ndb.Key])
    doc = minidom.parseString(xml_content)
    items = []
    keys = []
    parsed_url = urlparse(rss_url)
    base_url = '%s://%s' % (parsed_url.scheme, parsed_url.netloc)
    for item in doc.getElementsByTagName('item'):
        try:
            title = remove_html(html_unescape(item.getElementsByTagName("title")[0].firstChild.nodeValue)).strip()
            url = item.getElementsByTagName("link")[0].firstChild.nodeValue
            guid_elements = item.getElementsByTagName('guid')
            if guid_elements:
                guid = guid_elements[0].firstChild.nodeValue
            else:
                guid = None
            description_tags = item.getElementsByTagName("description")
            if not description_tags or not description_tags[0].firstChild:
                logging.debug('url: %s', url)
                logging.info('description not found or empty for %s', item.childNodes)
                continue
            description_html = description_tags[0].firstChild.nodeValue
            message = html_to_markdown(description_html, base_url)
            date_tags = item.getElementsByTagName('pubDate')
            image_url = get_image_url(item, description_html)
            if date_tags:
                date_str = item.getElementsByTagName('pubDate')[0].firstChild.nodeValue
                try:
                    date = datetime.fromtimestamp(rfc822.mktime_tz(rfc822.parsedate_tz(date_str)))
                except TypeError:
                    logging.debug('Could not parse date: %s', date_str)
                    date = dateutil.parser.parse(date_str, dayfirst=True)
                    if date.utcoffset():
                        # this date contains tzinfo and needs to be removed
                        epoch = get_epoch_from_datetime(date.replace(tzinfo=None)) + date.utcoffset().total_seconds()
                        date = datetime.utcfromtimestamp(epoch)
            else:
                date = None
        except:
            logging.debug(item.childNodes)
            logging.debug("url: %s", url)
            raise

        url_key = SolutionRssScraperItem.create_key(service_user, service_identity, url)
        # Always add url key for backwards compatibility - in the past only url was used as key
        keys.append(url_key)
        if guid:
            guid_key = SolutionRssScraperItem.create_key(service_user, service_identity, guid)
            keys.append(guid_key)

        items.append(ScrapedItem(title, url, guid, message, date, rss_url, image_url))
    return items, keys


def get_image_url(item, description_html):
    enclosure_tags = item.getElementsByTagName('enclosure')
    if enclosure_tags:
        for tag in enclosure_tags:
            if tag.getAttribute('type').startswith('image/'):
                return tag.getAttribute('url')
    media_tags = item.getElementsByTagName('media:content')
    if media_tags:
        for tag in media_tags:
            if tag.getAttribute('type').startswith('image/'):
                return tag.getAttribute('url')
    # As last resort try to parse the description
    if '<img' in description_html:
        doc = BeautifulSoup(description_html, features='lxml')
        img_tag = doc.find('img')
        if img_tag:
            return img_tag['src']
