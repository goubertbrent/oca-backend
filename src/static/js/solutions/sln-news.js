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

    var newsList = new NewsList('news', $('#page_news'));
    var newsWizard;

    function init() {
        if (LocalCache.serviceMenu) {
            newsWizard = new NewsWizard(newsList, {
                serviceMenu: LocalCache.serviceMenu,
            });
        } else {
            sln.call({
                url: '/common/get_menu',
                type: 'GET',
                success: function (serviceMenu) {
                    LocalCache.serviceMenu = serviceMenu;
                    newsWizard = new NewsWizard(newsList, {
                        serviceMenu: LocalCache.serviceMenu,
                    });
                }
            });
        }

        ROUTES.news = router;
        modules.news = {};
    }

    init();

    function router(urlHash) {
        var page = urlHash[1];
        if (['overview', 'edit', 'add'].indexOf(page) === -1) {
            page = 'add';
            window.location.hash = '#/' + urlHash[0] + '/' + page;
            return;
        }

        if (newsWizard && newsWizard.keepState) {
            newsWizard.keepState = false;
            BUDGET = null;
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
        modules.settings.getBroadcastOptions(function (broadcastOptions) {
            modules.broadcast.getAppStatistics(function (appStatistics) {
                modules.menu.getMenu(function (menu) {
                    if (orderSettings.order_type !== CONSTS.ORDER_TYPE_ADVANCED) {
                        menu = null;
                    }
                    modules.sandwich.getSandwichSettings(function (sandwichSettings) {
                        newsWizard.broadcastOptions = broadcastOptions;
                        newsWizard.appStatistics = appStatistics;
                        newsWizard.menu = menu;
                        newsWizard.sandwichSettings = sandwichSettings;
                        newsWizard.edit(newsId);
                    });
                });
            });
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
