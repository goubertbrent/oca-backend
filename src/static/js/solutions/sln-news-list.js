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
    this.items = []
    this.statistics = {};
    this.cursor = null;

    this.title = this.options.title || T('previous_news_items')
    this.baseLink = '#/' + this.tag;
    $(window).scroll(this.validateLoadMore.bind(this));
}


NewsList.prototype = {
    getElement: function(selector) {
        return $(selector, this.container);
    },

    getNativeElement: function(selector, at) {
        var idx = at ? at : 0;
        return this.getElement(selector)[idx];
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

    showMoreStatsClicked: function(event) {
        var dis = $(event.currentTarget);
        // buttons receive clicks even while they're disabled
        if(dis.attr('disabled')) return;

        var newsId = parseInt(dis.attr('news_id'));
        var property = dis.attr('property_name');
        var container = this.getElement('.show_more_stats_' + newsId);
        var containerHidden = container.css('display') == 'none';
        // same button is the button with green color
        // rgb(139, 197, 63) = #8bc53f
        var sameButton = dis.css('color') == 'rgb(139, 197, 63)';

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

          var stats = this.statistics[newsId];
          if(stats === undefined) {
              sln.call({
                    url: '/common/news/statistics',
                    data: {
                        news_id: newsId
                    },
                    type: 'GET',
                    success: function (newsItem) {
                        this.statistics[newsId] = newsItem.statistics;
                        spinner.remove();
                        this.renderStatistics(container, newsId, newsItem.statistics, property);
                    }.bind(this)
              });
          } else {
              spinner.remove();
              this.renderStatistics(container, newsId, stats, property);
          }
       }
    },

        /*
    fill the missing time data with the previous row value
    :param timeData: an array of time data
    */
    fillMissingTimeData: function (timeData) {
        var columns = Object.keys(timeData[0]).length;
        $.each(timeData, function (i, row) {
            var rowLength = Object.keys(row).length;
            if (rowLength < columns) {
                // row[0] is a date
                // timeData[i -1] is the previous row
                var prevRow = timeData[i - 1];
                for (var j = 1; j < columns; j++) {
                    if (row[j] === undefined) {
                        if(prevRow) {
                            row[j] = prevRow[j];
                        } else {
                            row[j] = 0;
                        }
                    }
                }
            }
        });
    },

    /*
    groups the time stats with day date instead of time

    :param timeStats: an array of stats objects {timestamp: xxxx, amount: xxx}

    :returns: a map with keys as date strings
              and values are amounts
    */
    groupTimeStatsByDay: function(timeStats) {
        var group = {};

        for(var i = 0; i < timeStats.length; i++) {
            // remove time part from the timestamp
            // so date would be only the day timestamp
            var date = new Date(timeStats[i].timestamp * 1000).setHours(0, 0, 0, 0);
            if(group[date] !== undefined) {
                group[date] += timeStats[i].amount;
            } else {
                group[date] = timeStats[i].amount;
            }
        }

        return group;
    },

    renderStatistics: function(container, newsId, statistics, property) {
        google.charts.load('current', {'packages': ['corechart', 'annotationchart']});
        google.charts.setOnLoadCallback(drawCharts.bind(this));
        function drawCharts() {
            var lineOptions = {
                  displayZoomButtons: false,
                  displayRangeSelector: false,
              },
              barOptions = {
                  title: T('age'),
                  legend: {
                      position: 'bottom'
                  },
                  width: 600,
                  hAxis: {
                      showTextEvery: 3
                  },
                  isStacked: true
              },
              pieOptions = {
                  title: T('gender'),
                  width: 300,
                  legend: {
                      position: 'bottom'
                  }
              };
            var ageData, genderData, timeData;
            // structure:
            // [
            //     ['App', 'rogerthat', 'be-loc'],
            //     ['0-5', 0, 42],
            //     ['5-10', 0, 420],
            // ]
            var hasGenderData = false;
            var regionalReach = 0;
            var defaultAppId = ACTIVE_APPS[0];
            for (var appCounter = 0; appCounter < statistics.length; appCounter++) {
                var statisticsInApp = statistics[appCounter];
                var appId = statisticsInApp.app_id;
                var stats = statisticsInApp[property];
                var j, len;
                if (appCounter === 0) {
                    ageData = [
                        [T('age')]
                    ];
                    genderData = [
                        [T('gender'), T(property)]
                    ];
                    timeData = [{
                        0: {label: T('Date'), type: 'date'}
                    }];
                    for (j = 0, len = stats.age.length; j < len; j++) {
                        ageData.push([stats.age[j].key]);
                    }
                    for (j = 0, len = stats.gender.length; j < len; j++) {
                        genderData.push([T(stats.gender[j].key), 0]);
                    }
                }
                var app = ALL_APPS.filter(function (p) {
                    return p.id === appId;
                })[0];
                var appName = app ? app.name : appId;
                ageData[0].push(appName);
                timeData[0][appCounter + 1] = appName;
                var totalAppReach = 0;
                for (j = 0; j < stats.age.length; j++) {
                    ageData[j + 1].push(stats.age[j].value);
                    totalAppReach += stats.age[j].value;
                }
                for (j = 0; j < stats.gender.length; j++) {
                    genderData[j + 1][1] += stats.gender[j].value;
                    hasGenderData = hasGenderData || genderData[j + 1][1] !== 0;
                }

                if (appId !== 'rogerthat' && appId !== defaultAppId) {
                    regionalReach += totalAppReach;
                }

                j = 0;
                var timeByDayDate = this.groupTimeStatsByDay(stats.time);
                var dayTimestamps = Object.keys(timeByDayDate).sort().map(function(key) {
                    return parseInt(key);
                });
                for(var ts = 0; ts < dayTimestamps.length; ts++) {
                    var dayTimestamp = dayTimestamps[ts];
                    if(timeData[j + 1]  === undefined) {
                        timeData[j + 1] = {
                            // must be date object in annotation charts
                            0: new Date(dayTimestamp)
                        };
                    }
                    // set amount
                    if(j > 0) {
                        // sum with previous amount if not the first
                        var prev = timeData[j][appCounter + 1];
                        timeData[j + 1][appCounter + 1] = prev + timeByDayDate[dayTimestamp];
                    } else {
                        timeData[j + 1][appCounter + 1] = timeByDayDate[dayTimestamp];
                    }
                    j++;
                }
            }

            // apps differ in recorded time amounts, also
            // time spans (app1: 5 months, app2: 1 year)...etc
            // this will fill the missing values
            // because the data is accumulative
            this.fillMissingTimeData(timeData);
            // append and show the divs first
            var template = $.tmpl(templates['broadcast/news_stats_row'],{
              news_id: newsId
            });
            container.append(template);

            var totalReachElem = this.getElement('.stats_regional_total_reach_' + newsId);
            if (regionalReach && property === 'reached') {
                totalReachElem.text(CommonTranslations.regional_reach + ': ' + regionalReach);
            } else {
                totalReachElem.hide();
            }

            var ageElem = this.getNativeElement('.stats_age_graph_' + newsId);
            var ageTable = google.visualization.arrayToDataTable(ageData);
            var ageChart = new google.visualization.ColumnChart(ageElem);
            ageChart.draw(ageTable, barOptions);
            var genderElem = this.getNativeElement('.stats_gender_graph_' + newsId);
            if (hasGenderData) {
                var genderTable = google.visualization.arrayToDataTable(genderData);
                var genderChart = new google.visualization.PieChart(genderElem);
                genderChart.draw(genderTable, pieOptions);
            } else {
                genderElem.innerHTML = '<i>' + T('not_enough_data') + '</i>';
            }
            var timeElem = this.getNativeElement('.stats_time_graph_' + newsId);
            $.each(timeData, function (i, td) {
                timeData[i] = $.map(td, function (value, index) {
                    return [value];
                });
            });
            if (timeData.length > 2) {
                var timeTable = google.visualization.arrayToDataTable(timeData);
                var timeChart = new google.visualization.AnnotationChart(timeElem);
                timeChart.draw(timeTable, lineOptions);
            }
        }
    }
};
