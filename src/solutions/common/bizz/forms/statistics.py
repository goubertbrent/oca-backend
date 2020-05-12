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

from datetime import datetime

from google.appengine.ext import ndb

from rogerthat.rpc import users
from rogerthat.service.api.forms import service_api
from rogerthat.to.forms import FormSectionValueTO, TextInputComponentValueTO, MultiSelectComponentValueTO, \
    DatetimeComponentValueTO, FileComponentValueTO, LocationComponentValueTO
from solutions.common.bizz.forms.util import remove_sensitive_answers
from solutions.common.models.forms import FormStatisticsShardConfig, FormStatisticsShard
from solutions.common.to.forms import FormStatisticsTO


def get_random_shard_number(form_id):
    shard_config_key = FormStatisticsShardConfig.create_key(form_id)
    shard_config = shard_config_key.get()
    if not shard_config:
        shard_config = FormStatisticsShardConfig(key=shard_config_key)
        shard_config.put()
    return shard_config.get_random_shard()


@ndb.transactional(xg=True)
def update_form_statistics(service_user, submission, shard_number):
    # type: (users.User, FormSubmission, int) -> None
    with users.set_user(service_user):
        form = service_api.get_form(submission.form_id)
    to_put = []
    shard = _update_form_statistics(submission, form, shard_number)
    submission.statistics_shard_id = shard.key.id()
    to_put.append(submission)
    to_put.append(shard)
    ndb.put_multi(to_put)


@ndb.transactional()
def _update_form_statistics(submission, form, shard_number):
    # type: (FormSubmission, DynamicFormTO, int) -> FormStatisticsShard
    shard_key = FormStatisticsShard.create_key(
        FormStatisticsShard.SHARD_KEY_TEMPLATE % (submission.form_id, shard_number))
    shard = shard_key.get()
    if not shard:
        shard = FormStatisticsShard(key=shard_key)
    sections = remove_sensitive_answers(form.sections, FormSectionValueTO.from_list(submission.sections))
    shard.data = _get_shard_data(shard.data or {}, sections)
    shard.count += 1
    return shard


def _get_shard_data(summarized_data, sections):
    # type: (dict, list[FormSectionValueTO]) -> dict
    for section in sections:
        if section.id not in summarized_data:
            summarized_data[section.id] = {}
        section_data = summarized_data[section.id]
        for component in section.components:
            if component.id not in section_data:
                section_data[component.id] = {}
            component_data = section_data[component.id]
            if isinstance(component, TextInputComponentValueTO):
                _increment_value_count(component_data, component.value)
            elif isinstance(component, MultiSelectComponentValueTO):
                for value in component.values:
                    _increment_value_count(component_data, value)
            elif isinstance(component, DatetimeComponentValueTO):
                if component.year == 0:
                    # format == 'time'
                    # 09:15 -> 915
                    val = component.hour * 100 + component.minute
                    _increment_value_count(component_data, val)
                else:
                    iso_str = datetime(year=component.year, month=component.month, day=component.day,
                                       hour=component.hour, minute=component.minute).isoformat() + 'Z'
                    _increment_value_count(component_data, iso_str)
            elif isinstance(component, FileComponentValueTO):
                if not isinstance(component_data, list):
                    component_data = []
                component_data.append(component.to_statistics())
            elif isinstance(component, LocationComponentValueTO):
                if not isinstance(component_data, list):
                    component_data = []
                component_data.append(component.to_statistics())
            section_data[component.id] = component_data
        summarized_data[section.id] = section_data
    return summarized_data


def _increment_value_count(dictionary, value):
    # avoid 'null' string as value
    if value is None:
        value = ''
    if value not in dictionary:
        dictionary[value] = 1
    else:
        dictionary[value] += 1
    return dictionary


def _decrement_value_count(dictionary, value):
    # avoid 'null' string as value
    if value is None:
        value = ''
    if value in dictionary:
        if dictionary[value] == 1:
            del dictionary[value]
        else:
            dictionary[value] -= 1
    return dictionary


def get_all_statistic_keys(form_id):
    keys = [FormStatisticsShardConfig.create_key(form_id)]
    keys.extend(FormStatisticsShardConfig.get_all_keys(form_id))
    return keys


@ndb.transactional()
def increase_shards(form_id, shard_count):
    """Increase the number of shards for a given sharded counter. """
    key = FormStatisticsShardConfig.create_key(form_id)
    config = key.get() or FormStatisticsShardConfig(key=key)
    if config.num_shards < shard_count:
        config.shard_count = shard_count
        config.put()


def get_form_statistics(form):
    # type: (Form) -> FormStatisticsTO
    shards = ndb.get_multi(FormStatisticsShardConfig.get_all_keys(form.id))  # type: list[FormStatisticsShard]

    # Summarize statistics from all shards into one object
    total_count = 0
    summarized = {}

    for shard in shards:
        if not shard:
            continue
        total_count += shard.count
        for section_id in shard.data:
            section_data = shard.data[section_id]
            if section_id not in summarized:
                summarized[section_id] = {}
            for component_id in section_data:
                component_data = section_data[component_id]
                if component_id not in summarized[section_id]:
                    summarized[section_id][component_id] = None
                for val in component_data:
                    if isinstance(val, list):
                        if not summarized[section_id][component_id]:
                            summarized[section_id][component_id] = [val]
                        else:
                            summarized[section_id][component_id].append(val)
                    elif isinstance(component_data[val], (int, long)):
                        if not summarized[section_id][component_id]:
                            summarized[section_id][component_id] = {
                                val: component_data[val]
                            }
                        else:
                            if val not in summarized[section_id][component_id]:
                                summarized[section_id][component_id][val] = component_data[val]
                            else:
                                summarized[section_id][component_id][val] += component_data[val]
    return FormStatisticsTO(submissions=total_count, statistics=summarized)


def remove_submission_from_shard(shard, submission):
    # type: (FormStatisticsShard, FormSubmission) -> FormStatisticsShard
    sections = FormSectionValueTO.from_list(submission.sections)
    shard.count -= 1
    for section in sections:
        section_data = shard.data.get(section.id)
        if not section_data:
            continue
        for component in section.components:
            component_data = section_data.get(component.id)
            if not component_data:
                continue
            if isinstance(component, TextInputComponentValueTO):
                _decrement_value_count(component_data, component.value)
            elif isinstance(component, MultiSelectComponentValueTO):
                for value in component.values:
                    _decrement_value_count(component_data, value)
            elif isinstance(component, DatetimeComponentValueTO):
                if component.year == 0:
                    # format == 'time'
                    # 09:15 -> 915
                    val = component.hour * 100 + component.minute
                    _decrement_value_count(component_data, val)
                else:
                    iso_str = datetime(year=component.year, month=component.month, day=component.day,
                                       hour=component.hour, minute=component.minute).isoformat() + 'Z'
                    _decrement_value_count(component_data, iso_str)
            elif isinstance(component, FileComponentValueTO):
                comp_stats = component.to_statistics()
                if not isinstance(component_data, list):
                    component_data = []
                component_data = [c for c in component_data if c != comp_stats]
            elif isinstance(component, LocationComponentValueTO):
                comp_stats = component.to_statistics()
                if not isinstance(component_data, list):
                    component_data = []
                component_data = [c for c in component_data if c != comp_stats]
            section_data[component.id] = component_data
        shard.data[section.id] = section_data
    return shard
