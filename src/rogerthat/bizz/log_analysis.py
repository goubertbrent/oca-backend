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

import datetime
import json
import logging
from collections import defaultdict

from google.appengine.api import logservice
from google.appengine.ext import deferred, db, ndb

from mcfw.utils import chunks
from rogerthat.dal import parent_key
from rogerthat.dal.profile import get_user_profile
from rogerthat.dal.service import count_users_connected_to_service_identity
from rogerthat.models import LogAnalysis, ServiceInteractionDef, ServiceAPIFailures, \
    ServiceIdentityStatistic, BroadcastStatistic, FlowStatistics
from rogerthat.models.news import NewsItem
from rogerthat.models.properties.news import NewsItemStatistics, NewsStatisticPerApp
from rogerthat.rpc import users
from rogerthat.utils import now, SLOG_HEADER
from rogerthat.utils.service import get_service_user_from_service_identity_user

QRCODE_SCANNED = "fti_qr_code_scanned"
SERVICE_MONITOR = "fti_monitor"
SERVICE_STATS = "fti_service_stats"
BROADCAST_STATS = "fti_broadcast_stats"
FLOW_STATS = "fti_flow_stats"
NEWS = "fti_news"

SERVICE_STATS_TYPE_GAINED = "gained"
SERVICE_STATS_TYPE_LOST = "lost"
SERVICE_STATS_TYPE_MIP = "menuItemPress"
SERVICE_STATS_TYPE_RECOMMEND_VIA_ROGERTHAT = "recommendViaRogerthat"
SERVICE_STATS_TYPE_RECOMMEND_VIA_EMAIL = "recommendViaEmail"

BROADCAST_STATS_SENT = "sent"
BROADCAST_STATS_RECEIVED = "received"
BROADCAST_STATS_READ = "read"

REQUEST_IDENTIFICATION = "request_identification"
REQUEST_IDENTIFICATION_TYPE_USER = "user"
REQUEST_IDENTIFICATION_TYPE_DEFERRED = "deferred"

NEWS_CREATED = "news.created"
NEWS_UPDATED = "news.updated"
NEWS_REACHED = "news.reached"
NEWS_ROGERED = "news.rogered"
NEWS_NEW_FOLLOWER = 'news.followed'
NEWS_ACTION = 'news.action'
NEWS_SPONSORING_TIMED_OUT = "news.sticky_timed_out"


def run():
    def trans():
        key_name = "log_analysis_instance"
        parent = parent_key(users.User(u"dashboard@rogerth.at"))
        la = LogAnalysis.get_by_key_name(key_name, parent)
        if not la:
            la = LogAnalysis(key_name=key_name, parent=parent, analyzed_until=now() - 10 * 60)
        start = la.analyzed_until
        end = now()
        la.analyzed_until = end
        db.put_async(la)
        deferred.defer(_analyze, start, end, _transactional=True)
    db.run_in_transaction(trans)


def _analyze(start, end):
    logging.debug('_analyze start:%s end:%s', start, end)
    from rogerthat.bizz import monitoring

    put_rpcs = defaultdict(list)

    def qr_code_scanned(request, log_entry, slog_entry, counters):
        params = slog_entry["a"]
        sid = params["sid"]
        if sid is None:
            return
        service_identity_email = params["service"]
        supported_platform = params["supported_platform"]
        from_rogerthat = params["from_rogerthat"]
        sid_key = (service_identity_email, sid)
        counters[sid_key] = counters.get(sid_key, dict(total=0, from_rogerthat=0, supported=0, unsupported=0))
        sid_counters = counters[sid_key]
        sid_counters["total"] += 1
        if from_rogerthat:
            sid_counters["from_rogerthat"] += 1
        else:
            sid_counters['supported' if supported_platform else 'unsupported'] += 1

    def store_stats_qr_scans(counters):
        sid_rpcs = list()
        for (service_identity_email, sid), sid_counters in counters.iteritems():
            sid_key = db.Key.from_path(ServiceInteractionDef.kind(), sid,
                                       parent=parent_key(get_service_user_from_service_identity_user(users.User(service_identity_email))))
            sid_rpcs.append((db.get_async(sid_key), sid_counters))
        for sid_rpc, sid_counters in sid_rpcs:
            sid = sid_rpc.get_result()
            sid.totalScanCount += sid_counters["total"]
            sid.scannedFromRogerthatCount += sid_counters["from_rogerthat"]
            sid.scannedFromOutsideRogerthatOnSupportedPlatformCount += sid_counters['supported']
            sid.scannedFromOutsideRogerthatOnUnsupportedPlatformCount += sid_counters['unsupported']
            put_rpcs['qr_scans'].append(db.put_async(sid))

    def service_api_failure(request, log_entry, slog_entry, counters):
        params = slog_entry["a"]
        service_identity_email = params["service"]
        call_type = params["call_type"]
        counters[service_identity_email] = counters.get(service_identity_email, dict(Call=0, CallBack=0))
        sie_counters = counters[service_identity_email]
        sie_counters[call_type] += 1

    def store_stats_api_failures(counters):

        keys = [ServiceAPIFailures.key_from_service_user_email(k) for k in counters.keys()]
        safs = db.get(keys)
        for i in xrange(len(keys)):
            key = keys[i]
            saf = safs[i]
            if not saf:
                saf = ServiceAPIFailures(key=key, creationTime=now(), failedCalls=0, failedCallBacks=0)
                safs[i] = saf
            saf.failedCalls += counters[key.name()][monitoring.SERVICE_API_CALL]
            saf.failedCallBacks += counters[key.name()][monitoring.SERVICE_API_CALLBACK]
        for chunk in chunks(safs, 200):
            db.put(chunk)

    def service_user_stats(request, log_entry, slog_entry, counters):
        params = slog_entry["a"]

        service_identity_user_email = params["service"]
        tag = params["tag"]
        type_ = params["type_"]
        counters[service_identity_user_email] = counters.get(service_identity_user_email, dict(
            gained=list(), lost=list(), menuItemPress=list(), recommendViaRogerthat=list(), recommendViaEmail=list()))
        sid_counters = counters[service_identity_user_email]
        sid_counters[type_].append(tag)

    def store_service_user_stats(counters):
        sid_rpcs = list()
        for (service_identity_user_email), sid_counters in counters.iteritems():
            sevice_identity_user = users.User(service_identity_user_email)
            sid_key = ServiceIdentityStatistic.create_key(sevice_identity_user)
            sid_rpcs.append((db.get_async(sid_key), sid_counters, sid_key, sevice_identity_user))
        for sid_rpc, sid_counters, sid_key, sevice_identity_user in sid_rpcs:
            sid = sid_rpc.get_result()
            new_sid = False
            if not sid:
                new_sid = True
                sid = ServiceIdentityStatistic(key=sid_key)
                sid.users_gained = list()
                sid.users_lost = list()
                sid.last_ten_users_gained = list()
                sid.last_ten_users_lost = list()
                sid.recommends_via_rogerthat = list()
                sid.recommends_via_email = list()
                sid.mip_labels = list()

            now_ = datetime.datetime.utcnow()
            today = int("%d%02d%02d" % (now_.year, now_.month, now_.day))
            if today != sid.last_entry_day:

                if new_sid:
                    add_days = 1
                else:
                    tmp = str(sid.last_entry_day)
                    start = datetime.date(int(tmp[0:4]), int(tmp[4:6]), int(tmp[6:8]))
                    end = datetime.date(now_.year, now_.month, now_.day)
                    delta = end - start
                    add_days = delta.days

                sid.last_entry_day = today

                def do(lst):
                    for _ in xrange(add_days):
                        lst.append(0)
                        if len(lst) > 1000:
                            lst.pop(0)

                do(sid.users_gained)
                do(sid.users_lost)
                do(sid.recommends_via_rogerthat)
                do(sid.recommends_via_email)
                for i in xrange(len(sid.mip_labels)):
                    do(getattr(sid, 'mip_%s' % i))

            gained = sid_counters[SERVICE_STATS_TYPE_GAINED]
            if new_sid:
                sid.number_of_users = count_users_connected_to_service_identity(sevice_identity_user)

            sid.last_ten_users_gained.extend(gained)
            sid.last_ten_users_gained = sid.last_ten_users_gained[-10:]
            sid.users_gained[-1] = sid.users_gained[-1] + len(gained)

            lost = sid_counters[SERVICE_STATS_TYPE_LOST]
            sid.last_ten_users_lost.extend(lost)
            sid.last_ten_users_lost = sid.last_ten_users_lost[-10:]
            sid.users_lost[-1] = sid.users_lost[-1] + len(lost)

            recommendsViaRogerthat = sid_counters[SERVICE_STATS_TYPE_RECOMMEND_VIA_ROGERTHAT]
            recommendsViaEmail = sid_counters[SERVICE_STATS_TYPE_RECOMMEND_VIA_EMAIL]

            sid.recommends_via_rogerthat[-1] = sid.recommends_via_rogerthat[-1] + len(recommendsViaRogerthat)
            sid.recommends_via_email[-1] = sid.recommends_via_email[-1] + len(recommendsViaEmail)

            if not new_sid:
                sid.number_of_users = sid.number_of_users + len(gained) - len(lost)

            sid.gained_last_week = sum(sid.users_gained[-7:])
            sid.lost_last_week = sum(sid.users_lost[-7:])

            for x in sid_counters[SERVICE_STATS_TYPE_MIP]:
                if x not in sid.mip_labels:
                    sid.mip_labels.append(x)
                    i = sid.mip_labels.index(x)
                    l = list()
                    l.append(1)
                    setattr(sid, 'mip_%s' % i, l)
                else:
                    i = sid.mip_labels.index(x)
                    l = getattr(sid, 'mip_%s' % i)
                    l[-1] = l[-1] + 1
                    setattr(sid, 'mip_%s' % i, l)

            put_rpcs['service_user_stats'].append(db.put_async(sid))

    def broadcast_stats(request, log_entry, slog_entry, counters):
        params = slog_entry["a"]
        service_identity_user_email = params["service"]
        type_ = params["type_"]
        broadcast_guid = params["broadcast_guid"]

        counters[broadcast_guid] = counters.get(
            broadcast_guid, dict(sent=0, received=0, read=0, service_identity_user_email=service_identity_user_email))
        sid_counters = counters[broadcast_guid]
        sid_counters[type_] += 1

    def store_broadcast_stats(counters):
        broadcast_stats_rpcs = list()
        for (broadcast_guid), broadcast_counters in counters.iteritems():
            service_identity_user = users.User(broadcast_counters["service_identity_user_email"])
            broadcast_statistic_key = BroadcastStatistic.create_key(broadcast_guid, service_identity_user)
            broadcast_stats_rpcs.append(
                (db.get_async(broadcast_statistic_key), broadcast_counters, broadcast_statistic_key, broadcast_guid, service_identity_user))
        for broadcast_stat_rpc, broadcast_counters, broadcast_statistic_key, broadcast_guid, service_identity_user in broadcast_stats_rpcs:
            broadcast_statistic = broadcast_stat_rpc.get_result()
            if not broadcast_statistic:
                broadcast_statistic = BroadcastStatistic(key=broadcast_statistic_key, timestamp=now())

            broadcast_statistic.sent = (broadcast_statistic.sent or 0) + broadcast_counters[BROADCAST_STATS_SENT]
            broadcast_statistic.received = (
                broadcast_statistic.received or 0) + broadcast_counters[BROADCAST_STATS_RECEIVED]
            broadcast_statistic.read = (broadcast_statistic.read or 0) + broadcast_counters[BROADCAST_STATS_READ]

            put_rpcs['broadcast_stats'].append(db.put_async(broadcast_statistic))

    def flow_stats(request, log_entry, slog_entry, counters):
        params = slog_entry['a']
        tag = params['tag']
        # Key names cannot begin and end with two underscores (__*__)
        if tag and not (tag.startswith("_") and tag.endswith("_")):
            service_identity_user = users.User(params['service_identity_user'])
            today = params['today']
            flow_stats_key = str(FlowStatistics.create_key(tag, service_identity_user))
            # counters: { flow_stats_key : { today : [(breadcrumbs, statuses, current_step_id, current_btn_id)] } }
            counters[flow_stats_key][today].append((params['breadcrumbs'],
                                                    params['statuses'],
                                                    params['current_step_id'],
                                                    params['current_btn_id']))

    def store_flow_stats(counters):
        to_put = list()
        flow_stats_keys = counters.keys()
        for flow_stats_key, flow_stats in zip(flow_stats_keys, db.get(flow_stats_keys)):
            if not flow_stats:
                flow_stats = FlowStatistics(key=flow_stats_key)
            to_put.append(flow_stats)
            for day, stats_list in sorted(counters[flow_stats_key].iteritems()):
                flow_stats.set_today(datetime.datetime.utcfromtimestamp(day).date())
                for breadcrumbs, statuses, current_step_id, current_btn_id in stats_list:
                    for status in statuses:
                        btn_id = current_btn_id if status == FlowStatistics.STATUS_ACKED else None
                        flow_stats.add(breadcrumbs, current_step_id, status, btn_id)
        for chunk in chunks(to_put, 200):
            put_rpcs['flow_stats'].append(db.put_async(chunk))

    def news_statistics(request, log_entry, slog_entry, counters):
        """counters = {caches_to_clear: {app_id_1, app_id_2...}
                       },
                       'news_to_update': {
                            '465489498': {
                                'rogerthat': {
                                    'stats_reached': 35,
                                    'stats_gender': [0, 3, 5],  # other, male, female
                                    'stats_time': [42, 32, 12, 14, 2, 0],  # per hour
                                    'stats_age': [0, 0, 0, 1, 0, 5, 5],  # 21 long, first elem = unknown age, 2nd = 0-5, 3rd: 5-10, ...
                                }
                            }
                        }
                       }
           }"""
        user_email = slog_entry['e'] if 'e' in slog_entry else None  # Should only be None for NEWS_SPONSORING_TIMED_OUT
        params = slog_entry['a']
        action = params['action']

        _now = now()
        if action in (NEWS_REACHED, NEWS_ROGERED, NEWS_NEW_FOLLOWER, NEWS_ACTION):
            app_id = params['app_id']
            user_profile = get_user_profile(users.User(user_email))
            if not user_profile:
                return
            age_index = NewsItemStatistics.get_age_index(user_profile.age)
            gender_index = NewsItemStatistics.get_gender_index(user_profile.gender)
            for news_id in params['news_ids']:
                if app_id not in counters['news_to_update'][news_id]:
                    counters['news_to_update'][news_id][app_id] = {}
                news_updates = counters['news_to_update'][news_id][app_id]
                if action == NEWS_REACHED:
                    news_updates['reached'] = news_updates.get('reached', 0) + 1
                elif action == NEWS_ROGERED:
                    users_that_rogered = news_updates.get('rogered', set())
                    users_that_rogered.add(users.User(user_email))
                    news_updates['rogered'] = users_that_rogered
                elif action == NEWS_NEW_FOLLOWER:
                    news_updates['follow_count'] = news_updates.get('follow_count', 0) + 1
                elif action == NEWS_ACTION:
                    news_updates['action_count'] = news_updates.get('action_count', 0) + 1

                stats_key = 'stats_%s' % action
                if stats_key not in news_updates:
                    news_updates[stats_key] = defaultdict(lambda: dict)
                news_updates[stats_key]['gender'] = news_updates[stats_key].get('gender',
                                                                                NewsItemStatistics.default_gender_stats())
                news_updates[stats_key]['gender'][gender_index] += 1
                news_updates[stats_key]['time'] = news_updates[stats_key].get('time', {})
                news_updates[stats_key]['time'][_now] = news_updates[stats_key]['time'].get(_now, 0) + 1
                news_updates[stats_key]['age'] = news_updates[stats_key].get('age',
                                                                             NewsItemStatistics.default_age_stats())
                news_updates[stats_key]['age'][age_index] += 1
        elif action == NEWS_CREATED:
            # add a new dict if news_id not yet in news_to_update (defaultdict)
            counters['news_to_update'][params['news_id']]
        elif action == NEWS_SPONSORING_TIMED_OUT:
            counters['news_to_update'][params['news_id']]['sticky_timed_out'] = True
        elif action == NEWS_UPDATED:
            counters['caches_to_clear']['app_ids'].update(params['app_ids'])

    def store_news_actions(counters):
        from rogerthat.bizz.news import setup_news_statistics_count_for_news_item, get_news_by_ids

        news_to_update = counters['news_to_update']
        news_ids = news_to_update.keys()
        news_ds_objects = get_news_by_ids(news_ids)
        news_items = {}
        for news_id, news_item in zip(news_ids, news_ds_objects):
            if news_item:
                news_items[news_id] = news_item
                if news_item.statistics is None:
                    news_item.statistics = NewsStatisticPerApp()
                    for app_id in news_item.app_ids:
                        news_item.statistics[app_id] = NewsItemStatistics.default_statistics()
            else:
                logging.warn('Skipping summarize for news item %s since it was not found.', news_id)

        for news_id, news_item in news_items.iteritems():
            updated = False
            assert (isinstance(news_item, NewsItem))
            news_item_datetime = datetime.datetime.utcfromtimestamp(news_item.timestamp)
            if news_item.follow_count < 0:
                setup_news_statistics_count_for_news_item(news_item)
                updated = True

            for app_id, update in news_to_update[news_id].iteritems():
                if app_id == 'sticky_timed_out':
                    sponsoring_timed_out = update
                    if sponsoring_timed_out and news_item.sticky:
                        news_item.sticky = False
                        updated = True
                        continue

                reached = update.get('reached')
                if reached:
                    news_item.reach += reached
                    updated = True

                rogered = update.get('rogered')
                if rogered:
                    news_item.rogered = True
                    news_item.users_that_rogered.extend(rogered)
                    updated = True

                follow_count = update.get('follow_count')
                if follow_count:
                    news_item.follow_count += follow_count
                    updated = True

                action_count = update.get('action_count')
                if action_count:
                    news_item.action_count += action_count
                    updated = True

                for action in (NEWS_REACHED, NEWS_ROGERED, NEWS_NEW_FOLLOWER, NEWS_ACTION):
                    added_statistics = update.get('stats_%s' % action)
                    if added_statistics:
                        updated = True
                        key = action.replace('news.', '')
                        for prop in ('age', 'gender', 'time'):
                            statistic_property = '%s_%s' % (key, prop)
                            default_stats = getattr(NewsItemStatistics, 'default_%s_stats' % prop)()
                            original_statistics = getattr(news_item.statistics[app_id], statistic_property,
                                                          default_stats)
                            if prop == 'time':
                                # This is a dict instead of a list
                                for timestamp, value in added_statistics[prop].iteritems():
                                    item_date = datetime.datetime.utcfromtimestamp(timestamp)
                                    hour_index = NewsItemStatistics.get_time_index(news_item_datetime, item_date)
                                    diff = hour_index - len(original_statistics) + 1
                                    for i in xrange(diff):
                                        original_statistics.append(0)
                                    original_statistics[hour_index] += value
                            else:
                                for i, value in enumerate(added_statistics[prop]):
                                    original_statistics[i] += value

                            if news_item.statistics[app_id] is None:
                                news_item.statistics[app_id] = NewsItemStatistics.default_statistics()
                            setattr(news_item.statistics[app_id], statistic_property, original_statistics)

                if not updated:
                    del news_items[news_id]  # don't include in db.put

        if len(news_items):
            logging.info('Summarize: updating %d news items\n%s', len(news_items), news_items.keys())
            for chunk in chunks(news_items.values(), 200):
                put_rpcs['news_stats'].extend(ndb.put_multi_async(chunk))

    amap = {
        QRCODE_SCANNED: dict(analysis_func=qr_code_scanned, summarize_func=store_stats_qr_scans,
                             counters=dict()),
        SERVICE_MONITOR: dict(analysis_func=service_api_failure, summarize_func=store_stats_api_failures,
                              counters=dict()),
        SERVICE_STATS: dict(analysis_func=service_user_stats, summarize_func=store_service_user_stats,
                            counters=dict()),
        BROADCAST_STATS: dict(analysis_func=broadcast_stats, summarize_func=store_broadcast_stats,
                              counters=dict()),
        FLOW_STATS: dict(analysis_func=flow_stats, summarize_func=store_flow_stats,
                         counters=defaultdict(lambda: defaultdict(list))),
        NEWS: {
            'analysis_func': news_statistics,
            'summarize_func': store_news_actions,
            'counters': {
                'news_to_update': defaultdict(dict),
                'caches_to_clear': {
                    'news': set(),
                    'app_ids': set()
                }
            }
        },
    }

    slog_header_length = len(SLOG_HEADER)

    offset = None
    while True:
        logs = logservice.fetch(start_time=start, end_time=end, offset=offset,
                                minimum_log_level=logservice.LOG_LEVEL_INFO, include_incomplete=False,
                                include_app_logs=True)
        count = 0
        for log in logs:
            count += 1
            offset = log.offset
            for app_log in log.app_logs:
                if app_log.message and app_log.message.startswith(SLOG_HEADER):
                    slog_value = app_log.message[slog_header_length + 1:]
                    try:
                        slog_value = json.loads(slog_value)
                    except:
                        logging.exception("Failed to parse slog entry:\n%s" % slog_value)
                        continue
                    ftie = slog_value.get("f", None)
                    if not ftie:
                        continue
                    analyzer = amap.get(ftie, None)
                    if not analyzer:
                        continue
                    analyzer["analysis_func"](log, app_log, slog_value, analyzer["counters"])
        if count == 0:
            break

    # summarize could be paralellized in the future. See http://docs.python.org/library/queue.html
    try:
        key = None
        for mapping in amap.itervalues():
            mapping["summarize_func"](mapping["counters"])
        for key, rpc_list in put_rpcs.iteritems():
            for rpc_item in rpc_list:
                rpc_item.get_result()
    except:
        logging.exception("Failed to execute summarize of '%s'!" % key, _suppress=False)
