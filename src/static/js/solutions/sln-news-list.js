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

function NewsList(tag, container, options) {
    this.tag = tag;
    this.container = container;
    this.options = options || {};

    this.isLoadingNews = false;
    this.hasMoreNews = false;
    this.items = [];
    this.newsItems = {};
    this.cursor = null;

    this.title = this.options.title || T('previous_news_items')
    this.baseLink = '#/' + this.tag;
    $(window).scroll(this.validateLoadMore.bind(this));
}


NewsList.prototype = {
    getElement: function(selector) {
        return $(selector, this.container);
    },

    loadNews: function(loadMore) {
        if (loadMore) {
            this.container.append(TMPL_LOADING_SPINNER);
            this.getElement('.load_more_news').hide();
        } else {
            this.container.html(TMPL_LOADING_SPINNER);
        }
        if (!this.isEmpty() && !loadMore) {
            this.renderItems(this.items);
        } else {
            this.isLoadingNews = true;
            var self = this;
            var data = {
                cursor: loadMore ? self.cursor : null,
                tag: self.tag,
            }
            sln.call({
                url: '/common/news',
                data: data,
                type: 'GET',
                success: function (result) {
                    self.items = self.items.concat(result.result);
                    self.cursor = result.cursor;
                    self.hasMoreNews = result.result.length > 0;
                    self.renderItems(self.items);
                    self.isLoadingNews = false;
                },
                error: function () {
                    self.container.html(T('error_while_loading_news_try_again_later'));
                    self.isLoadingNews = false;
                }
            });
        }
    },

    count: function() {
        return this.items.length;
    },

    isEmpty: function() {
        return this.count() == 0;
    },

    getItem: function(newsId) {
        return this.items.filter(function(item) {
            return item.id === newsId;
        })[0];
    },

    addItem: function(newsItem) {
        this.items.unshift(newsItem);
    },

    renderItems: function(newsItems) {
        newsItems.map(function (n) {
            n.datetime = sln.format(new Date(n.timestamp * 1000));
        });
        var html = $.tmpl(templates['broadcast/broadcast_news_overview'], {
            title: this.title,
            baseLink: this.baseLink,
            newsItems: newsItems,
            scheduledAt: scheduledAt
        });
        this.container.html(html);
        this.getElement('.load_more_news').click(this.validateLoadMore.bind(this)).toggle(this.hasMoreNews);
        this.getElement('.delete_news_button').click(this.deleteItem.bind(this));
        this.getElement('.show_more_stats_button').click(this.showMoreStatsClicked.bind(this));

        function scheduledAt(datetime) {
            return T('scheduled_for_datetime', {datetime: sln.format(new Date(datetime * 1000))});
        }

        // show more news if the last news item is visible
        this.validateLoadMore();
    },

    validateLoadMore: function() {
        var lastNewsItem = this.getElement('.news-card').last();
        if(sln.isOnScreen(lastNewsItem) && this.hasMoreNews && !this.isLoadingNews) {
            this.loadNews(true);
        }
    },

    deleteItem: function(event) {
        var dis = $(event.currentTarget);
        var newsId = parseInt(dis.attr('news_id'));
        var newsItem = this.items.filter(function (n) {
            return n.id === newsId;
        })[0];
        if (!newsItem || newsItem.published) {
            dis.remove();
            return;
        }
        confirmDeleteNews(function () {
            sln.call({
                url: '/common/news/delete',
                method: 'post',
                data: {
                    news_id: newsId
                },
                success: success
            });
        });

        function confirmDeleteNews(callback) {
            var msg = T('confirm_delete_news', {news_title: newsItem.title || newsItem.qr_code_caption});
            sln.confirm(msg, callback);
        }

        var success = function(response) {
            if (!response.success) {
                sln.alert(response.error || T('error-occured-unknown-try-again'));
            } else {
                dis.remove();
                this.getElement('.news_item_' + newsId).remove();
                // remove the news item from cache
                var newsItemIndex = $.inArray(newsItem, this.items);
                if( newsItemIndex > -1) {
                    this.items.splice(newsItemIndex, 1);
                }
            }
        }.bind(this);
    },

    showMoreStatsClicked: function (event) {
        var dis = $(event.currentTarget);
        // buttons receive clicks even while they're disabled
        if (dis.attr('disabled')) return;

        var newsId = parseInt(dis.attr('news_id'));
        var property = dis.attr('property_name');
        var container = this.getElement('.show_more_stats_' + newsId);
        var containerHidden = container.css('display') === 'none';
        // same button is the button with green color
        // rgb(139, 197, 63) = #8bc53f
        var sameButton = dis.css('color') === 'rgb(139, 197, 63)';

        // empty container and set all buttons to the default color
        this.getElement('.show_more_stats_button[news_id=' + newsId + ']').css('color', '');
        container.empty();

        // hide only if the same button clicked
        if (!containerHidden && sameButton) {
            container.slideUp();
        } else {
            var spinner = $(TMPL_LOADING_SPINNER).css('position', 'relative');
            container.append(spinner);
            container.slideDown();
            // color the button with green
            dis.css('color', '#8bc53f');

            if (newsId in this.newsItems) {
                spinner.remove();
                this.renderStatistics(container, newsId, this.newsItems[newsId], property);
            } else {
                sln.call({
                    url: '/common/news/statistics',
                    data: {
                        news_id: newsId
                    },
                    type: 'GET',
                    success: function (result) {
                        this.newsItems[newsId] = result;
                        spinner.remove();
                        this.renderStatistics(container, newsId, result, property);
                    }.bind(this)
                });
            }
        }
    },

    renderStatistics: function (container, newsId, result, property, appId) {
        var self = this;
        var statistics = result.news_item.statistics;
        google.charts.load('current', {'packages': ['corechart']});
        google.charts.setOnLoadCallback(drawCharts.bind(this));

        function getTotal(property, subProperty, statsInApp, acc, keyKey, valueKey) {
            for (var i = 0; i < statsInApp[property][subProperty].length; i++) {
                var propValue = statsInApp[property][subProperty][i];
                var key = propValue[keyKey];
                var value = propValue[valueKey];
                acc[subProperty][key] = (acc[subProperty][key] || 0) + value;
            }
            return acc;
        }

        /**
         * Converts statistics from 'value on timestamp' to a cumulative sum of all previous values
         */
        function cumulativeSum(cumulative, statsOnTime) {
            var date = statsOnTime[0];
            var value = statsOnTime[1];
            cumulative.push([date, (cumulative.length && cumulative[cumulative.length - 1][1] || 0) + value]);
            return cumulative;
        }

        function createChartData(statistics) {
            // Combine stats from all items in case appId is not set, else only get stats from one app.
            var stats = statistics.filter(function (s) {
                return appId ? s.app_id === appId : true;
            }).reduce(function (acc, statsInApp) {
                acc.total += statsInApp[property].total;
                acc = getTotal(property, 'gender', statsInApp, acc, 'key', 'value');
                acc = getTotal(property, 'age', statsInApp, acc, 'key', 'value');
                acc = getTotal(property, 'time', statsInApp, acc, 'timestamp', 'amount');
                return acc;
            }, {age: {}, gender: {}, time: {}, total: 0});
            var defaultAppId = ACTIVE_APPS[0];
            var regionalReach = statistics.filter(function (s) {
                return s.app_id !== defaultAppId && s.app_id !== 'rogerthat';
            }).reduce(function (appAcc, s) {
                return appAcc + s.reached.gender.reduce(function (genderAcc, genderStat) {
                    return genderAcc + genderStat.value;
                }, 0);
            }, 0);

            var ageData = [
                [T('age'), T('amount')]
            ].concat(Object.keys(stats.age).map(function (age) {
                return [age === '0 - 5' ? T('unknown') : age, stats.age[age]];
            }));
            var genderData = [
                [T('gender'), T('amount')]
            ].concat(Object.keys(stats.gender).map(function (gender) {
                return [T(gender), stats.gender[gender]];
            }));
            var timeStats = Object.keys(stats.time).map(function (timestamp) {
                return [new Date(timestamp * 1000), stats.time[timestamp]];
            }).reduce(cumulativeSum, []);
            var timeData = [
                [T('Date'), T('amount')]
            ].concat(timeStats);
            return {regionalReach: regionalReach, ageData: ageData, genderData: genderData, timeData: timeData};

        }

        function drawCharts() {
            var chartData = createChartData(statistics);
            // append and show the divs first
            var template = $.tmpl(templates['broadcast/news_stats_row'],{
                news_id: newsId,
                T: T,
                reach: chartData.regionalReach,
                showReach: property === 'reached',
                apps: [{id: '', name: T('all_apps')}].concat(result.apps),
                selectedApp: appId,
            });
            container.html(template);
            $('#stats_app_selector_' + newsId).change(function () {
                var appId = $(this).val();
                self.renderStatistics(container, newsId, statistics, property, appId);
            });

            var ageWrapper = new google.visualization.ChartWrapper({
                chartType: 'ColumnChart',
                dataTable: google.visualization.arrayToDataTable(chartData.ageData),
                options: {
                    title: T('age'),
                    legend: {
                        position: 'none'
                    },
                    width: 600,
                    hAxis: {
                        showTextEvery: 3
                    },
                    isStacked: true,
                    animation: {duration: 1000, easing: 'out', startup: true}
                },
                containerId: 'stats_age_graph_' + newsId
            });
            ageWrapper.draw();
            var genderData = chartData.genderData;
            var hasGenderData = genderData.length === 4 && genderData[1][1] + genderData[2][1] + genderData[3][1] !== 0;
            if (hasGenderData) {
                var genderWrapper = new google.visualization.ChartWrapper({
                    chartType: 'PieChart',
                    dataTable: google.visualization.arrayToDataTable(genderData),
                    options: {
                        title: T('gender'),
                        width: 300,
                        legend: {
                            position: 'bottom'
                        }
                    },
                    containerId: 'stats_gender_graph_' + newsId
                });
                genderWrapper.draw();
            } else {
                $('#stats_gender_graph_' + newsId).html('<i>' + T('not_enough_data') + '</i>');
            }
            if (chartData.timeData.length > 2) {
                var timeWrapper = new google.visualization.ChartWrapper({
                    chartType: 'LineChart',
                    dataTable: google.visualization.arrayToDataTable(chartData.timeData),
                    options: {
                        width: 900,
                        explorer: {
                            actions: ['dragToZoom', 'rightClickToReset'],
                            axis: 'horizontal',
                            keepInBounds: true,
                            maxZoomIn: 0.1
                        },
                        legend: {position: 'none'},
                        animation: {duration: 1000, easing: 'out', startup: true}
                    },
                    containerId: 'stats_time_graph_' + newsId
                });
                timeWrapper.draw();
            }
        }
    }
};
