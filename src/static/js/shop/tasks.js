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

$(function() {
    "use strict";
    var COLORS = [ '#f3e1f5', '#d9edf7', '#dff0d8', '#fcf8e3' ];
    var ICONS = {
        1 : 'fa-map-marker',
        2 : 'fa-phone',
        3 : 'fa-question'
    };

    var taskLists = {};

    var loadProspect = function(prospectId) {
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
    };

    var loadTasks = function (assignees) {
        assignees = assignees || [];
        var appId = $('#filter-by-app').val() || 'all';
        var taskType = parseInt($('#filter-by-type').val()) || undefined;
        if (assignees.length === 0) {
            $('#task-container').empty();
            taskLists = {};
            showProcessing('Loading tasks...');
        }

        sln.call({
            url : '/internal/shop/rest/task/list',
            type : 'POST',
            data : {
                data : JSON.stringify({
                    assignees: assignees,
                    app_id: appId,
                    task_type: taskType
                })
            },
            success : function(data) {
                var now = new Date().getTime() / 1000;
                $.each(data, function(i, taskList) {
                    if (taskLists[taskList.assignee]) {
                        taskList.color = taskLists[taskList.assignee].color;
                    } else {
                        taskList.color = COLORS[i % COLORS.length];
                    }
                    taskLists[taskList.assignee] = taskList;
                    $.each(taskList.tasks, function(j, task) {
                        task.execution_time_str = getDateString(new Date(1000 * task.execution_time));
                        task.icon = ICONS[task.type];
                        task.in_past = task.execution_time < now;
                    });
                });

                renderTasks(assignees, data);

                if (assignees.length == 0) {
                    hideProcessing();
                }
            },
            error : function() {
                if (assignees.length == 0) {
                    hideProcessing();
                    showError('An unknown error occurred. Check with the administrators.');
                } else {
                    showError('An error occurred while updating the task list of [' + assignees.join(', ')
                            + ']. Check with the administrators.');
                }
            }
        });
    };

    var renderTasks = function(assignees, data) {
        if (!assignees || assignees.length === 0) {
            var html = $.tmpl(JS_TEMPLATES.task_list, {
                task_lists: data
            });
            $('#task-container').append(html);
        } else {
            $.each(assignees, function(i, assignee) {
                if (!taskLists[assignee]) {
                    return true;
                }
                var html = $.tmpl(JS_TEMPLATES.task_list, {
                    task_lists : [ taskLists[assignee] ]
                });

                var oldTable = $('#task-container table[data-assignee="' + assignee + '"]');
                if (oldTable.length) {
                    oldTable.after(html).remove();
                } else {
                    $('#task-container').append(html);
                }
            });
        }

        $('.edit-task').unbind('click').click(function() {
            $(this).parents('tr').click();
        });

        $('#task-table tbody tr').unbind('click').click(function() {
            var prospectId = $(this).attr('data-prospect-id');
            loadProspect(prospectId);
        });
    };

    var channelUpdates = function(data) {
        console.log("channel update from tasks:", data);
        if (data.type == 'shop.task.updated') {
            loadTasks(data.assignees);
        } else if (data.type == 'shop.prospect.updated') {
            var assignees = [];

            $.each(taskLists, function(assignee, taskList) {
                $.each(taskList.tasks, function(i, task) {
                    if (task.prospect_id == data.prospect.id) {
                        task.prospect_name = data.prospect.name;
                        task.comments = sln.map(data.prospect.comments, function(comment) {
                            return comment.text
                        });
                        if (assignees.indexOf(assignee) == -1) {
                            assignees.push(assignee);
                        }
                    }
                });
            });
            renderTasks(assignees);

            // If the infoPopup of this prospect is shown, then it will be updated by prospects.js
        }
    };

    loadTasks();

    $('#filter-by-app, #filter-by-type').change(function () {
        loadTasks();
    });

    sln.registerMsgCallback(channelUpdates);
});
