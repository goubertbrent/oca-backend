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

$(function() {
    'use strict';
    var teams;

    $(document).on('click', '#questions_table .assign-team', function() {
        var questionId = parseInt($(this).attr('question_id'));
        var teamId = parseInt($(this).attr('team_id'));
        getTeams(showSelectTeamModal, questionId, teamId);
    });

    function getTeams(callback, questionId, teamId) {
        if(teams) {
            callback(teams, questionId, teamId);
        } else {
            sln.call({
                url: '/internal/shop/rest/regio_manager_team/list',
                type: 'get',
                success: function(teams) {
                    callback(teams, questionId, teamId);
                },
                error: sln.showAjaxError
            });
        }
    }

    function reload(modal) {
        if(modal) {
            moda.modal('hide');
        }
        window.location.reload();
    }

    function showSelectTeamModal(teams, questionId, teamId) {
        var html = $.tmpl(JS_TEMPLATES.teams_select_modal, {
            teams: teams,
            selectedTeam: teamId
        });

        var modal = sln.createModal(html);
        $('button[action=submit]', modal).click(function() {
            var teamId = parseInt($('#team_select').val());

            sln.call({
                url: '/internal/shop/rest/question/assign',
                type: 'post',
                data: {
                    team_id: teamId,
                    question_id: questionId
                },
                success: function(result) {
                    if(result.success) {
                        sln.alert('An E-Mail has been sent to the support manager', reload, 'Sucess');
                    } else {
                        sln.alert(result.errormsg, reload, 'Failed');
                    }
                },
                error: sln.showAjaxError
            });
        });
    }

});
