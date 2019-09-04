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

import base64
from collections import defaultdict
import json
import logging

import cloudstorage
from google.appengine.ext import db
from mapreduce import mapreduce_pipeline
from mapreduce.main import pipeline
from pipeline.common import List

from rogerthat.bizz.job.send_unread_messages import CleanupGoogleCloudStorageFiles
from rogerthat.consts import MIGRATION_QUEUE, DEBUG, PIPELINE_BUCKET
from rogerthat.dal import parent_key_unsafe
from rogerthat.dal.app import get_app_by_id
from rogerthat.models import ServiceIdentityStatistic, ServiceIdentity
from rogerthat.settings import get_server_settings
from rogerthat.utils import now, send_mail
from rogerthat.utils.service import create_service_identity_user
from solutions.common import SOLUTION_COMMON
from solutions.common.models.loyalty import SolutionLoyaltySettings, SolutionLoyaltyVisitRevenueDiscount, \
    SolutionLoyaltyVisitLottery, SolutionLoyaltyVisitStamps, SolutionCityWideLotteryVisit


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def export(email):

    def update():
        now_ = now()
        key = "ExportCityServicesPipeline-%s" % (now_)
        counter = ExportCityServicesPipeline(key, email)
        task = counter.start(idempotence_key=key, return_task=True)
        task.add(queue_name=MIGRATION_QUEUE, transactional=True)

        redirect_url = "%s/status?root=%s" % (counter.base_path, counter.pipeline_id)
        logging.info("export pipeline url: %s", redirect_url)

    db.run_in_transaction(update)


class ExportCityServicesPipeline(pipeline.Pipeline):

    def run(self, key, email):
        mapper_params = {
            "entity_kind": "shop.models.Customer"
        }
        reducer_params = {
            "output_writer": {
                "bucket_name": PIPELINE_BUCKET,
            }
        }

        output = yield mapreduce_pipeline.MapreducePipeline(
            job_name=key,
            mapper_spec="shop.exports.jobs.customer_map",
            mapper_params=mapper_params,
            combiner_spec="rogerthat.bizz.job.send_unread_messages.unread_message_combine",
            reducer_spec="rogerthat.bizz.job.send_unread_messages.unread_message_reduce",
            reducer_params=reducer_params,
            input_reader_spec="rogerthat.bizz.job.send_unread_messages.DatastoreQueryInputReader",
            output_writer_spec="mapreduce.output_writers.GoogleCloudStorageConsistentOutputWriter",
            shards=1 if DEBUG else None)

        customer_pipeline = yield CustomerPipeline(output, email)
        with pipeline.After(customer_pipeline):
            yield CleanupGoogleCloudStorageFiles(output)

    def finalized(self):
        if self.was_aborted:
            logging.error("ExportCityServicesPipeline was aborted", _suppress=False)
            return
        logging.info("ExportCityServicesPipeline was finished")


def customer_map(c):
    if not c or not c.service_email:
        return
    if not c.default_app_id or not c.default_app_id.startswith('be-'):
        return
    app = get_app_by_id(c.default_app_id)
    if app.ios_app_id in (None, '-1'):
        return

    loyalty_type = ''
    loyalty_actions_count = ''
    if c.has_loyalty:
        sln_l_settings_key = SolutionLoyaltySettings.create_key(c.service_user)
        sln_l_settings = db.get(sln_l_settings_key)
        if sln_l_settings:
            parent_key = parent_key_unsafe(c.service_user, SOLUTION_COMMON)
            if sln_l_settings.loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_REVENUE_DISCOUNT:
                loyalty_type = 'Revenue discount'
                loyalty_actions_count = SolutionLoyaltyVisitRevenueDiscount.all().ancestor(parent_key).count(None)
            elif sln_l_settings.loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_LOTTERY:
                loyalty_type = 'Lottery'
                loyalty_actions_count = SolutionLoyaltyVisitLottery.all().ancestor(parent_key).count(None)
            elif sln_l_settings.loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_STAMPS:
                loyalty_type = 'Stamps'
                loyalty_actions_count = SolutionLoyaltyVisitStamps.all().ancestor(parent_key).count(None)
            elif sln_l_settings.loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_CITY_WIDE_LOTTERY:
                loyalty_type = 'City'
                city_ancestor_key = SolutionCityWideLotteryVisit.create_city_parent_key(app.app_id)
                service_ancestor_key = db.Key.from_path(SOLUTION_COMMON, c.service_user.email(),
                                                        parent=city_ancestor_key)
                loyalty_actions_count = SolutionLoyaltyVisitStamps.all().ancestor(service_ancestor_key).count(None)

    sis_key = ServiceIdentityStatistic.create_key(create_service_identity_user(c.service_user,
                                                                               identity=ServiceIdentity.DEFAULT))
    sis = db.get(sis_key)

    v = {
        'VAT': c.vat or '',
        'USERS': sis.number_of_users if sis else 0,
        'NAME': c.name,
        'EMAIL': c.user_email,
        'STREET': c.address1,
        'CITY': c.city,
        'LOYALTY-TYPE': loyalty_type,
        '#ACTIONS': loyalty_actions_count
    }
    yield (app.name, json.dumps(v))


class CustomerPipeline(pipeline.Pipeline):

    def run(self, output, email):
        results = list()
        for filename in output:
            results.append((yield CustomerFilePipeline(filename)))
        results.append(email)
        yield List(*results)

    def finalized(self):
        import xlwt

        email = self.outputs.default.value.pop()

        def stretch(lijsten):
            for lijst in lijsten:
                for value in lijst:
                    yield value

        stats = defaultdict(list)
        for d in stretch(self.outputs.default.value):
            for v in d['value']:
                stats[d['key']].append(json.loads(v))

        loyalty_pattern = xlwt.Pattern()
        loyalty_pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        loyalty_pattern.pattern_fore_colour = 41

        loyalty_style = xlwt.XFStyle()
        loyalty_style.pattern = loyalty_pattern

        book = xlwt.Workbook(encoding="utf-8")

        sheet_total = book.add_sheet('Total')
        sheet_total.write(0, 0, len(stats))
        sheet_total.write(0, 1, 'Total Cities')
        sheet_total.write(1, 0, sum((sum(c['USERS'] for c in customers) for customers in stats.itervalues())))
        sheet_total.write(1, 1, 'Total City-Users')
        sheet_total.write(2, 0, sum(len(customers) for customers in stats.itervalues()))
        sheet_total.write(2, 1, 'Total City-Services')
        sheet_total.write(3, 0, sum(sum(1 for c in customers if c['LOYALTY-TYPE']) for customers in stats.itervalues()))
        sheet_total.write(3, 1, 'Total Loyalty Services')

        for app_name in sorted(stats.iterkeys()):
            customers = stats[app_name]

            sheet_app = book.add_sheet(app_name)
            for i, w in enumerate((5000, 5000, 10000, 8000, 8000, 4000, 4000, 4000)):
                sheet_app.col(i).width = w

            sheet_app.write(0, 0, sum(c['USERS'] for c in customers))
            sheet_app.write(0, 1, 'City-Users')
            sheet_app.write(1, 0, len(customers))
            sheet_app.write(1, 1, 'City-Services')
            sheet_app.write(2, 0, sum(1 for c in customers if c['LOYALTY-TYPE']), loyalty_style)
            sheet_app.write(2, 1, 'Loyalty Services', loyalty_style)

            row = 4
            for col, value in enumerate(("VAT", "USERS", "NAME", "EMAIL", "STREET", "CITY", "LOYALTY-TYPE", "#ACTIONS")):
                sheet_app.write(row, col, value)

            for c in customers:
                row += 1
                style = loyalty_style if c['LOYALTY-TYPE'] else xlwt.Style.default_style
                for col, value in enumerate(("VAT", "USERS", "NAME", "EMAIL", "STREET", "CITY", "LOYALTY-TYPE", "#ACTIONS")):
                    sheet_app.write(row, col, c[value], style)

        excel_file = StringIO()
        book.save(excel_file)
        excel_string = excel_file.getvalue()

        to = [email]
        subject = body = 'Export city services'
        attachments = []
        attachments.append(('export_city_services_%s.xls' % (now()),
                            base64.b64encode(excel_string)))
        send_mail(get_server_settings().senderEmail, to, subject, body, attachments=attachments)


class CustomerFilePipeline(pipeline.Pipeline):

    def run(self, filename):
        results = list()
        with cloudstorage.open(filename, "r") as f:
            for json_line in f:
                d = json.loads(json_line)
                results.append(d)

        yield List(*results)
