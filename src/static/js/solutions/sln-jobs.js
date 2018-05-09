/*
 * Copyright 2017 Mobicage NV
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * @@license_version:1.2@@
 */

$(function () {
    'use strict';

    var newsList = new NewsList('jobs', $('#page_jobs'), {
        title: T('previous_job_ads')
    });
    var newsWizard;

    function init() {
        newsWizard = new NewsWizard(newsList, {
            title: T('jobs'),
            defaultButtons: [{
                label: T('like'),
            }, {
                label: T('share'),
            }, {
                label: T('respond'),
                is_action: true,
            }],
            steps: [{
                text: T('Content'),
                description: T('news_content_explanation'),
                tab: 1,
            }, {
                text: T('Label'),
                description: T('jobs_label_explanation'),
                tab: 3,
            }, {
                text: T('delayed_broadcast'),
                description: T('jobs_schedule_explanation'),
                tab: 5,
            }, {
                text: T('target_audience'),
                description: T('news_target_audience_explanation'),
                tab: 6,
            }, {
                text: T('checkout'),
                description: '',
                tab: 7
            }],
            translations: {
                item_saved: 'jobs_item_saved',
                item_published: 'jobs_item_published',
                item_scheduled: 'jobs_item_scheduled_for_datetime',
                item_publish_error: 'could_not_publish_job_ad',
            }
        });

        ROUTES.jobs = router;
    }

    init();

    function router(urlHash) {
        var page = urlHash[1];
        if (['overview', 'edit', 'add'].indexOf(page) === -1) {
            page = 'add';
            window.location.hash = '#/' + urlHash[0] + '/' + page;
            return;
        }

        if (page === 'overview') {
            newsList.loadNews();
        } else if (page === 'edit') {
            showEdit(urlHash[2]);
        } else if (page === 'add') {
            showEdit();
        }
    }

    function showEdit(newsId) {
        modules.settings.getBroadcastOptions(function (broadcastOptions) {
            modules.broadcast.getAppStatistics(function (appStatistics) {
                newsWizard.broadcastOptions = broadcastOptions;
                newsWizard.appStatistics = appStatistics;
                newsWizard.edit(newsId);
            });
        });
    }

});
