/*
 * Copyright 2019 Green Valley Belgium NV
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
 * @@license_version:1.5@@
 */

google.load("visualization", "1.1", {packages: ['bar', 'line']});
google.setOnLoadCallback(getSalesStats);
var baseURL = '/internal/shop/rest/';
var stats = [], currentStats = [], currentTeamId = null;
var CHARTTYPES = { BAR: 'bar', LINE: 'line' };
var PERIOD = { MONTH: 'month', DAY: 'day' };
var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
var DEBUG = window.location.hostname.match(/^10\.|^192\.168|^localhost/) ? true : false;
var lines = [
    'So far, {{manager}} had the most success this month, gathering {{amount}} in total.'
    // <insert motivational lines here>
];
var barChart, lineChart;

function getSalesStats() {
    if (DEBUG) console.time('get_sales_stats');
    sln.call({
        url: baseURL + 'salesstats/load',
        method: 'get',
        success: function (data) {
            stats = data;
            if (DEBUG) console.timeEnd('get_sales_stats');
            loadSalesStats();
            $('#stats_loading').hide();
        }
    });
}
function setCurrentStats(){
    currentStats = [];
    $.each(stats, function (i, regioManagerStats) {
        if(regioManagerStats.show_in_stats) {
            var filterRegioManager = false;
            if (currentTeamId && regioManagerStats.team_id) {
                if (currentTeamId != regioManagerStats.team_id) {
                    filterRegioManager = true;
                }
            }
            if (!filterRegioManager) {
                currentStats.push(regioManagerStats);
            }
        }
    });
}

function loadSalesStats () {
    if (regioManagerTeams.length) {
        _loadSalesStats();
    } else {
        setTimeout(loadSalesStats, 200);
    }
}

function _loadSalesStats () {
    setCurrentStats();
    if (!currentTeamId) {
        var teamIds = [];
        $.each(stats, function (i, regioManagerStats) {
            if (regioManagerStats.team_id && teamIds.indexOf(regioManagerStats.team_id) == -1) {
                teamIds.push(regioManagerStats.team_id);
            }
        });
        
        if (teamIds.length > 1) {
            var select = $("#teams");
            select.empty();
            select.append($('<option></option>').attr('value', "").text("Select team"));
            var teams = regioManagerTeams.filter(function (t) {
                return teamIds.indexOf(t.id) !== -1;
            });
            $.each(teams, function (i, team) {
                select.append($('<option></option>').attr('value', team.id).text(team.name));
            });
            select.show();
        }
    }
    renderSales(CHARTTYPES.BAR, PERIOD.MONTH, 1, 'month_chart');
    setCurrentStats();
    var length;
    if (currentStats[0]) {
        var minDate = undefined;
        var maxDate = undefined;
        for (var i = 0; i < currentStats.length; i++) {
            var revenue = currentStats[i].month_revenue;
            for (var j = 0; j < revenue.length; j++) {
                if (j % 2 == 0) {
                    var val = revenue[j].toString();
                    var date = new Date(val.substring(0, 4), val.substring(4, 6) - 1);
                    if (minDate == undefined || date < minDate) {
                        minDate = date;
                    }
                    if (maxDate == undefined || date > maxDate) {
                        maxDate = date;
                    }
                }
            }
        }
        length = 1 + (maxDate.getFullYear() - minDate.getFullYear()) * 12 - minDate.getMonth() + maxDate.getMonth();
    }
    
    setTimeout(function(){ // charts api probably does some asynchronous stuff.
        renderSales(CHARTTYPES.LINE, PERIOD.MONTH, length ? length: 1, 'sales_chart');
    }, 200);
}

function filterUndefined(o) {
    return !!o;
}

function getDataTable(type, length){
    //Filter out regio managers who did not earn anything
    var now = new Date();
    if(type === PERIOD.MONTH) {
        var pastDate = new Date(now.getFullYear(), now.getMonth() - length + 1, 1);
    }else{
        var pastDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - length);
    }
    var pastDateFormatted = parseInt(pastDate.getFullYear().toString() + ("0" + (pastDate.getMonth() +1)).slice(-2));

    if(length === 1){
        for (var i = 0, len = currentStats.length; i < len; i++) {
            var index = currentStats[i][type + '_revenue'].indexOf(pastDateFormatted); // no currentStats for this month yet for this manager
            if(index !== -1){
                if(currentStats[i][type + '_revenue'][index +1] == 0) { // revenue for this month is 0
                    delete currentStats[i];
                }
            }else{
                delete currentStats[i];
            }
        }
    }else {
        for (var i = 0, len = currentStats.length; i < len; i++) {
            var has_revenue = false;
            for (var j = 0, len2 = currentStats[i][type + '_revenue'].length; j < len2; j++) {
                if (j % 2 && currentStats[i][type + '_revenue'][j]) {
                    has_revenue = true;
                    break;
                }
            }
            if (!has_revenue) {
                delete currentStats[i];
            }
        }
    }
    currentStats = currentStats.filter(filterUndefined);

    data = [];
    data.push([]);
    data[0][0] = '';

    // Original:
    // 201503 0 201504 0 ...
    // 201503 15000 201504 12300 ...
    // 201503 52000 201504 45600 ...
    // 201503 65000 201504 78900 ...
    // 201503 45000 201504 98700 ...

    // Converted:
    //  date  man1  man2   man3   man4   man5 (man = manager, revenue in euro)
    // 201503  0   15000  52000  65000  45000
    // 201504  0   12300  45600  78900  98700
    var best_manager = {
        amount:0,
        name:''
    };
    var totalSalesAmount = 0;
    for(var i = 0, len= currentStats.length; i < len; i++){ // Manager loop
        var manager = currentStats[i].manager.split('@')[0].toString();
        manager = manager.charAt(0).toUpperCase() + manager.slice(1);
        data[0][i + 1] = manager;
        if (length == 1) {
            // last month statistics.Only get the last value of each array.
            // Also check if it really is this month's statistics, and not from last month.
            if (currentStats[i][type + '_revenue'].indexOf(pastDateFormatted) !== -1) {
                if (!data[1]) {
                    // set date
                    data[1] = [pastDate];
                }
                var index = currentStats[i][type + '_revenue'].indexOf(pastDateFormatted);
                data[1][i + 1] = currentStats[i][type + '_revenue'][index + 1];
                totalSalesAmount += data[1][i + 1];
                if (!best_manager.name || best_manager.amount < data[1][i + 1]) {
                    best_manager = {
                        name: manager,
                        amount: data[1][i + 1]
                    }
                }
            }
        } else {
            for (var j = 0, len2 = currentStats[i][type + '_revenue'].length; j < len2; j++) { // month loop
                var val = currentStats[i][type + '_revenue'][j].toString();
                var date;
                var dateInt;
                if (!(j % 2)) {
                    if (type == PERIOD.MONTH) {
                        date = new Date(val.substring(0, 4), val.substring(4, 6) - 1);
                        dateInt = parseInt(val);
                    }
                }
                if (date > pastDate || !pastDate) {
                    if (j % 2) { // values
                        data[dateInt][i + 1] = currentStats[i][type + '_revenue'][j];
                    } else if (!data[dateInt]) {// dates
                        data[dateInt] = [ date ];
                    }
                }
            }
        }
    }
    if(length === 1) {
        var line = lines[Math.floor(Math.random() * lines.length)];
        $('#sales_remark').html(line
            .replace('{{amount}}', '<strong>'+ best_manager.amount + '</strong>')
            .replace('{{manager}}', '<strong>' + best_manager.name + '</strong>'));
        $('#sales_total').text(totalSalesAmount);
        $('#sales_total_container').show();

    }
    data = data.filter(filterUndefined); // Remove undefined elements
    // Fill up empty values (when one manager has sold in a new month, but one or more other managers haven't)
    for (var i = 0, len = data.length; i < len; i++) {
        for (var j = 0, len2 = currentStats.length + 1; j < len2; j++) {
            if (data[i][j] === undefined) {
                data[i][j] = 0;
            }
        }
    }
    return google.visualization.arrayToDataTable(data);
}

function renderSales(type, period, length, elementIdentifier){
    if (DEBUG) console.time('render_sales');
    var data = getDataTable(period, length);
    var width = $(window).width() -50;
    var options = {
        chart: {
            title: length == 1 ? 'This month\'s sales revenue per manager, in euro' : 'Sales revenue per regional manager, in euro'
        },
        width: width,
        height: 400,
        legend: {position: 'bottom', alignment: 'start', maxLines: 1} // doesn't work for whatever reason
    };
    if (length === 1) {
        if (width < currentStats.length * 150){
            options.width = currentStats.length * 75;
        }else {
            options.width = currentStats.length * 150;
        }
        options.width = Math.max(200, options.width); // minimum 200px wide
    }
    var chart;
    if(period === PERIOD.MONTH){
        if (length > 12){
            options.hAxis = {
                format: ['MMM yyyy']
            };
        }else {
            options.hAxis = {
                format: ['MMMM']
            };
        }
    }
    if (CHARTTYPES.BAR === type) {
        if(length > 12){
            options.isStacked = true;
        }
        // Prevent the charts api from re-loading all the fonts required to draw this
        if (!barChart) {
            barChart = new google.charts.Bar(document.getElementById(elementIdentifier));
        }
        barChart.draw(data, options);
    }else if(CHARTTYPES.LINE === type){
        options.lineWidth = 5;
        if (!lineChart) {
            lineChart = new google.charts.Line(document.getElementById(elementIdentifier));
        }
        lineChart.draw(data, options);
    }
    if (DEBUG) console.timeEnd('render_sales');
}

$(document).ready(function(){
    var timeout;
    $(window).resize(function(){
        // prevent re-drawing while resizing
        if(stats.length) {
            clearTimeout(timeout);
            timeout = setTimeout(loadSalesStats, 200);
        }
    });
    
    $('#teams').change(function () {
        var select = $(this);
        var teamId = select.val();
        if (teamId) {
            currentTeamId = teamId;
        } else {
            currentTeamId = null;
        }
        loadSalesStats();
    });
});
