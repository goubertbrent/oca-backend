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

$(function() {
    var COLORS = [ '#f3e1f5', '#d9edf7', '#dff0d8', '#fcf8e3' ];
    var ICONS = {
        1 : 'icon-map-marker',
        2: 'icon-headphones',
        3: 'fa-question'

    };
    var datepicker, now;

    var taskLists = {};

    function loadProspect(prospectId) {
        showProcessing('Loading prospect...');
        sln.call({
            url : '/internal/shop/rest/prospects/detail',
            data : {
                prospect_id : prospectId
            },
            success : function(data) {
                hideProcessing();
                if (data) {
                    showProspectInfo(data);
                } else {
                    showError('Prospect does not exist');
                }
            },
            error : function() {
                hideProcessing();
                showError('An unknown error occurred. Check with the administrators.');
            }
        });
    }

    function loadTasks(date) {
        var dateFrom, dateTo;
        var curDate = parseInt(new Date().getTime()) / 1000;
        showProcessing('Loading ');

        if(!date) {
            date = now;
        }
        dateFrom = getFirstDayOfMonth(date);
        dateTo = getLastDayOfMonth(dateFrom);
        sln.call({
            url : '/internal/shop/rest/history/tasks',
            data : {
                // use current date if no date was provided
                date_from: dateFrom.getTime() / 1000,
                date_to: dateTo.getTime() / 1000
            },
            type : 'GET',
            success : function(data) {
                $.each(data, function(i, taskList) {
                    if (taskLists[taskList.assignee]) {
                        taskList.color = taskLists[taskList.assignee].color;
                    } else {
                        taskList.color = COLORS[i % COLORS.length];
                    }
                    taskLists[taskList.assignee] = taskList;
                    $.each(taskList.tasks, function(j, task) {
                        task.execution_time_str = getDateString(new Date(1000 * task.execution_time));
                        task.closed_time = getDateString(new Date(task.closed_time * 1000));
                        task.icon = ICONS[task.type];
                        task.in_past = task.execution_time < curDate;
                    });
                });

                renderTasks(data);
                hideProcessing();
            },
            error : function() {
                hideProcessing();
                showError('An unknown error occurred. Check with the administrators.');
            }
        });
    }

    function renderTasks(data) {
        var html = $.tmpl(JS_TEMPLATES.history_tasks, {
            task_lists : data
        });
        $('#task-container').html(html);
        $('.edit-task').unbind('click').click(function() {
            $(this).parents('tr').click();
        });

        $('#task-table tbody tr').unbind('click').click(function() {
            var prospectId = $(this).attr('data-prospect-id');
            loadProspect(prospectId);
        });
    }

    function initialize() {
        var nowTemp = new Date();
        now = new Date(nowTemp.getFullYear(), nowTemp.getMonth(), nowTemp.getDate(), 0, 0, 0, 0);
        datepicker = $('#history-date').datepicker({
            format: 'mm-yyyy',
            viewMode: 'months',
            minViewMode: 'months',
            onRender : function(date) {
                return date.valueOf() > now.valueOf() ? 'disabled' : '';
            }
        }).on('changeDate', function(ev) {
            // fetch tasks for the selected date
            datepicker.hide();
            // selected date with months mode is the first day of the month
            loadTasks(datepicker.date);
        }).data('datepicker');
        datepicker.setValue(now);
        // initialize buttons
        $('#date-prev').click(function() {
            changeDate(-1);
        });
        $('#date-next').click(function() {
            changeDate(1);
        });
        $('#date-reset').click(function() {
            changeDate(true);
        });
    }

    /*
     * Changes the date in the datepicker and fetches new results for that month
     *
     */
    function changeDate(months) {
        if (months === true) {
            datepicker.setValue(now);
        } else {
            var tempDate = datepicker.date;
            tempDate.setMonth(tempDate.getMonth() + months);
            datepicker.setValue(tempDate);
        }
        loadTasks(datepicker.date);
    }

    function getFirstDayOfMonth(date) {
        return new Date(date.getFullYear(), date.getMonth(), 1);
    }

    function getLastDayOfMonth(date) {
        return new Date(date.getFullYear(), date.getMonth() + 1, 0, 23, 59, 59);
    }

    initialize();
    loadTasks();
});
