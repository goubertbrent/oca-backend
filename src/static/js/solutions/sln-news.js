/*
 * Copyright 2018 Mobicage NV
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
 * @@license_version:1.3@@
 */

$(function () {
    'use strict';

    var newsPageElem = $('#page_news');
    newsPageElem.html(TMPL_LOADING_SPINNER);
    var newsList = new NewsList('news', newsPageElem);
    var newsWizard;

    function init() {
        Requests.getServiceMenu().then(function (serviceMenu) {
            createNewsWizard(serviceMenu);
        });

        ROUTES.news = router;
        modules.news = {};
    }

    init();

    function createNewsWizard(serviceMenu) {
        if (typeof NewsWizard === "undefined") {
            setTimeout(function () {
                createNewsWizard(serviceMenu);
            }, 200);
        } else {
            newsWizard = new NewsWizard(newsList, {
                serviceMenu: serviceMenu,
            });
        }
    }

    function router(urlHash) {
        var page = urlHash[1];
        if (['overview', 'edit', 'add'].indexOf(page) === -1) {
            page = 'add';
            window.location.hash = '#/' + urlHash[0] + '/' + page;
            return;
        }
        if (newsWizard && newsWizard.keepState) {
            newsWizard.keepState = false;
            newsWizard.showBudget();
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
        if (!newsWizard) {
            setTimeout(function () {
                showEdit(newsId);
            }, 200);
            return;
        }
        var broadcastPromise = Requests.getBroadcastOptions();
        var appStatsPromise = Requests.getAppStatistics();
        var sandwichSettingsPromise = Requests.getSandwichSettings();
        var menuPromise = Requests.getMenu();
        var orderSettingsPromise = Requests.getOrderSettings();
        // Execute 5 requests in parallel
        var promises = [broadcastPromise, appStatsPromise, sandwichSettingsPromise, menuPromise, orderSettingsPromise];
        Promise.all(promises).then(function (results) {
            var broadcastOptions = results[0],
                appStatistics = results[1],
                sandwichSettings = results[2],
                menu = results[3],
                orderSettings = results[4];
            if (orderSettings.order_type !== CONSTS.ORDER_TYPE_ADVANCED) {
                menu = null;
            }
            newsWizard.broadcastOptions = broadcastOptions;
            newsWizard.appStatistics = appStatistics;
            newsWizard.menu = menu;
            newsWizard.sandwichSettings = sandwichSettings;
            newsWizard.edit(newsId);
        });
    }

    modules.news.getEstimatedReach = function(reach) {
        // 1/8th - 1/4th
        return [Math.round(reach * 0.125), Math.round(reach * 0.25)].join(' - ');
    };

    modules.news.getEstimatedCost = function(reach, currency) {
        var maxCost = reach * 50.00 / 10000;
        // 1/8th - 1/4th
        return [currency, (maxCost * 0.125).toFixed(2), '-', currency, (maxCost * 0.25).toFixed(2)].join(' ');
    };
});
