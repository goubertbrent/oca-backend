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

import logging
import rfc822
from datetime import datetime
from urlparse import urlparse

import dateutil.parser
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from google.appengine.api import urlfetch
from google.appengine.ext import webapp, ndb
from xml.dom import minidom

from mcfw.properties import unicode_property, typed_property
from rogerthat.bizz.job import run_job
from rogerthat.consts import HIGH_LOAD_WORKER_QUEUE
from rogerthat.models.news import NewsGroup
from rogerthat.to import TO
from rogerthat.to.push import remove_html
from rogerthat.utils import now, get_epoch_from_datetime
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks
from solutions.common.cron.news import html_unescape, \
    create_news_item, update_news_item, news_item_hash, delete_news_item, \
    is_html
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionRssScraperSettings, SolutionRssScraperItem
from solutions.common.utils import html_to_markdown

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
        if not rss_link.group_type or rss_link.group_type not in (NewsGroup.TYPE_CITY,
                                                                  NewsGroup.TYPE_PROMOTIONS,
                                                                  NewsGroup.TYPE_EVENTS,
                                                                  NewsGroup.TYPE_TRAFFIC,
                                                                  NewsGroup.TYPE_PRESS,
                                                                  NewsGroup.TYPE_PUBLIC_SERVICE_ANNOUNCEMENTS,):
            logging.error("process_rss_links failed for '%s' and url '%s' invalid group_type found '%s'",
                          service_user,
                          rss_link.url,
                          rss_link.group_type)
            can_delete = False
            continue

        app_ids = rss_link.app_ids if rss_link.app_ids else None
        if rss_link.group_type == NewsGroup.TYPE_PRESS:
            feed_name = u'press'
        else:
            feed_name = None

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

        items, keys = parse_rss_items(response.content, rss_link.url, service_user, service_identity)
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
                    tasks.append(create_task(update_news_item, item.news_id, sln_settings, rss_link.group_type,
                                             scraped_item.message, scraped_item.title, scraped_item.url,
                                             scraped_item.image_url))
                    item.hash = scraped_item.hash
                    to_put.append(item)
            else:
                new_key = SolutionRssScraperItem.create_key(service_user, service_identity, scraped_item.id)
                new_item = SolutionRssScraperItem(key=new_key,
                                                  timestamp=now(),
                                                  dry_run=False,
                                                  hash=scraped_item.hash,
                                                  date=scraped_item.date,
                                                  rss_url=scraped_item.rss_url)
                
                if not dry_run and scraped_item.date and scraped_item.date < last_week_datetime:
                    logging.debug('new_outdated_news_item guid:%s url:%s', scraped_item.guid, scraped_item.url)
                elif dry_run and len(new_news_item_ids) > 100:
                    logging.debug('new_dry_run_max_items_reached guid:%s url:%s', scraped_item.guid, scraped_item.url)
                    new_item.dry_run = True
                else:
                    new_news_item_ids.append(scraped_item.id)
                    logging.debug('create_news_item guid:%s url:%s', scraped_item.guid, scraped_item.url)
                    timestamp = None
                    if scraped_item.date:
                        set_date = False
                        if dry_run:
                            set_date = True
                        else:
                            current_date = datetime.now()
                            if scraped_item.date.year == current_date.year and scraped_item.date.month == current_date.month and scraped_item.date.day == current_date.day:
                                set_date = True
                        if set_date:
                            timestamp = get_epoch_from_datetime(scraped_item.date)
                            if timestamp > now():
                                timestamp = None

                    tasks.append(create_task(create_news_item, sln_settings, rss_link.group_type, scraped_item.message,
                                             scraped_item.title, scraped_item.url, False if dry_run else rss_settings.notify,
                                             scraped_item.image_url, new_key, app_ids=app_ids, feed_name=feed_name, timestamp=timestamp))
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
        # type: (str, str, str, str, datetime, str, str) -> ScrapedItem
        self.title = title
        self.url = url
        self.guid = guid
        self.id = guid or url
        self.message = message
        self.date = date
        self.rss_url = rss_url
        self.image_url = image_url
        self.hash = news_item_hash(title, message, image_url)


def parse_rss_items(xml_content, rss_url, service_user=None, service_identity=None):
    # type: (str, str, users.User, str) -> ([ScrapedItem], [ndb.Key])
    try:
        doc = minidom.parseString(xml_content)
    except:
        logging.warn('Failed to parse xml_content', exc_info=True)
        logging.debug(xml_content)
        return [], []

    root_tag = doc.firstChild.tagName
    if root_tag == 'rss':
        return _flavor_rss_items(doc, rss_url, service_user=service_user, service_identity=service_identity)
    elif root_tag == 'feed':
        return _flavor_atom_items(doc, rss_url, service_user=service_user, service_identity=service_identity)

    logging.error(u'Unknown rss flavor %s', root_tag)
    return [], []


def scandown( elements, indent ):
    for el in elements:
        logging.debug("   " * indent + "nodeName: %s" % el.nodeName )
        logging.debug("   " * indent + "nodeValue: %s" % el.nodeValue )
        logging.debug("   " * indent + "childNodes: ")
        logging.debug(el.childNodes)
        scandown(el.childNodes, indent + 1)

def _get_date(current_date, date_str):
    logging.debug('date_str: %s', date_str)
    try:
        date = datetime.fromtimestamp(rfc822.mktime_tz(rfc822.parsedate_tz(date_str)))
    except TypeError:
        logging.debug('rfc822.parsedate_tz failed to resolve the date')
        date = dateutil.parser.parse(date_str, dayfirst=True)
        if date.utcoffset() is not None:
            # this date contains tzinfo and needs to be removed
            epoch = get_epoch_from_datetime(date.replace(tzinfo=None)) + date.utcoffset().total_seconds()
            date = datetime.utcfromtimestamp(epoch)

        if date > current_date:
            logging.debug('dayfirst must have switched the dates, continue without')
            date = dateutil.parser.parse(date_str)
            if date.utcoffset() is not None:
                # this date contains tzinfo and needs to be removed
                epoch = get_epoch_from_datetime(date.replace(tzinfo=None)) + date.utcoffset().total_seconds()
                date = datetime.utcfromtimestamp(epoch)

            if date > current_date:
                logging.debug('date still bigger ... continue with date None')
                date = None

    if date:
        # If the time it not known (00:00) for new items fetched on the same day,
        # fill in the time with the current time. That way it's at least semi-accurate.
        if date.year == current_date.year and date.month == current_date.month and date.day == current_date.day:
            if date.hour == 0 and date.minute == 0 and date.second == 0:
                date = date.replace(hour=current_date.hour, minute=current_date.minute)
        logging.debug('date_str.result: %s', date.strftime('%Y-%m-%d_%H:%M:%S'))

    return date

def _flavor_rss_items(doc, rss_url, service_user=None, service_identity=None):
    items = []
    keys = []
    parsed_url = urlparse(rss_url)
    base_url = '%s://%s' % (parsed_url.scheme, parsed_url.netloc)
    current_date = datetime.now()

    for item in doc.getElementsByTagName('item'):
        try:
            title = remove_html(html_unescape(item.getElementsByTagName("title")[0].firstChild.nodeValue)).strip()
            url = item.getElementsByTagName("link")[0].firstChild.nodeValue.strip()
            guid_elements = item.getElementsByTagName('guid')
            if guid_elements:
                guid = guid_elements[0].firstChild.nodeValue.strip()
            else:
                guid = None
            description_tags = item.getElementsByTagName("description")
            if not description_tags:
                logging.debug('url: %s', url)
                logging.info('description not found for %s', item.childNodes)
                continue
#             scandown(description_tags, 0)
            description_html = None
            for description_child in description_tags[0].childNodes:
                v = description_child.nodeValue.strip()
                if v:
                    description_html = v
                    break
            if not description_html:
                logging.debug('url: %s', url)
                logging.info('description empty for %s', item.childNodes)
                continue
            if not is_html(description_html):
                description_html = u'<br/>'.join(description_html.splitlines())
            message = html_to_markdown(description_html, base_url)
            date_tags = item.getElementsByTagName('pubDate')
            image_url = get_image_url(item, description_html)
            if date_tags:
                date_str = item.getElementsByTagName('pubDate')[0].firstChild.nodeValue
                date = _get_date(current_date, date_str)
            else:
                date = None
        except:
            logging.debug(item.childNodes)
            logging.debug("url: %s", url)
            raise

        if service_user:
            url_key = SolutionRssScraperItem.create_key(service_user, service_identity, url)
            # Always add url key for backwards compatibility - in the past only url was used as key
            keys.append(url_key)
            if guid:
                guid_key = SolutionRssScraperItem.create_key(service_user, service_identity, guid)
                keys.append(guid_key)

        items.append(ScrapedItem(title, url, guid, message, date, rss_url, image_url))
    return items, keys


def _flavor_atom_items(doc, rss_url, service_user=None, service_identity=None):
    items = []
    keys = []
    parsed_url = urlparse(rss_url)
    base_url = '%s://%s' % (parsed_url.scheme, parsed_url.netloc)
    current_date = datetime.now()

    for element in doc.getElementsByTagName('entry'):
        to = AtomEntry.from_element(element)
        if not to:
            continue

        date = None
        date_str = to.updated or to.published
        if date_str:
            date = _get_date(current_date, date_str)
        url = None
        image_url = None
        for link in to.links:
            if link.rel == 'alternate':
                url = link.href
            elif link.rel == 'enclosure' and link.type_.startswith('image/'):
                image_url = link.href

        description = None
        if to.summary:
            description = to.summary.value
        if to.content:
            if to.content.type_ in ('text',):
                description = to.summary.value
            elif to.content.type_ in ('html', 'xhtml',):
                description_html = to.content.value
                if not is_html(description_html):
                    description_html = u'<br/>'.join(description_html.splitlines())
                description = html_to_markdown(description_html, base_url)

        if not description:
            continue

        if service_user:
            if url:
                # Always add url key for backwards compatibility - in the past only url was used as key
                url_key = SolutionRssScraperItem.create_key(service_user, service_identity, url)
                keys.append(url_key)
            guid_key = SolutionRssScraperItem.create_key(service_user, service_identity, to.id_)
            keys.append(guid_key)

        items.append(ScrapedItem(to.title.value, url or to.id_, to.id_, description, date, rss_url, image_url))
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
            return img_tag['src'].decode('utf8')


def get_elements_by_tag(element, tag):
    return [i for i in element.getElementsByTagName(tag)]


class AtomText(TO):
    type_ = unicode_property('type')
    value = unicode_property('value')

    @classmethod
    def from_element(cls, element):
        to = cls()
        to.type_ = element.getAttribute('type')
        to.value = remove_html(html_unescape(element.firstChild.nodeValue)).strip()
        return to


class AtomLink(TO):
    href = unicode_property('href')
    rel = unicode_property('rel')
    title = unicode_property('title')
    type_ = unicode_property('type')

    @classmethod
    def from_element(cls, element):
        to = cls()
        to.href = element.getAttribute('href')
        to.rel = element.getAttribute('rel')
        to.title = element.getAttribute('title')
        to.type_ = element.getAttribute('type')
        return to


class AtomEntry(TO):
    title = typed_property('title', AtomText, False)
    id_ = unicode_property('id')

    published = unicode_property('published', default=None)
    updated = unicode_property('updated', default=None)

    links = typed_property('links', AtomLink, True, default=[])
    summary = typed_property('summary', AtomText, False, default=None)
    content = typed_property('content', AtomText, False, default=None)

    @classmethod
    def from_element(cls, element):
        to = cls()

        title_elements = get_elements_by_tag(element, 'title')
        if not title_elements:
            logging.debug('no title_elements')
            return None
        to.title = AtomText.from_element(title_elements[0])

        id_elements = get_elements_by_tag(element, 'id')
        if not id_elements:
            logging.debug('no id_elements')
            return None
        to.id_ = id_elements[0].firstChild.nodeValue

        published_elements = get_elements_by_tag(element, 'published')
        to.published = published_elements[0].firstChild.nodeValue if published_elements else None

        updated_elements = get_elements_by_tag(element, 'updated')
        to.updated = updated_elements[0].firstChild.nodeValue if updated_elements else None

        link_elements = get_elements_by_tag(element, 'link')
        to.links = [AtomLink.from_element(link) for link in link_elements]

        summary_elements = get_elements_by_tag(element, 'summary')
        content_elements = get_elements_by_tag(element, 'content')
        if not summary_elements and not content_elements:
            logging.debug('no summary_elements or content_elements')
            return None
        if summary_elements:
            to.summary = AtomText.from_element(summary_elements[0])
        if content_elements:
            to.content = AtomText.from_element(content_elements[0])

        return to
