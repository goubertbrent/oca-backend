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

var AccessType = {
    NO : "no",
    READ_ONLY : "read-only",
    FULL : "full"
};
var COLORS = [ '#d9edf7', '#dff0d8', '#fcf8e3' ];

$(function() {
    var apps = {};
    var unused_app_ids = [];
    var teams = {}
    var regioManagers = {};
    var unassignedRegioManagerEmails = [];

    var editRegioManagerTeam = function(teamId) {
        var team = teamId ? teams[teamId] : null;
        var modal = $('#regio-manager-team-info').modal('show').data('team_id', teamId);
        $('#regiomanagerteam_name', modal).val(team ? team.name : '');
        $('#regiomanagerteam_legal_entity', modal).val(team ? team.legal_entity_id : '');


        var tbody = $('#apps tbody', modal).empty();

        var possibleAppIds = [];
        if (team) {
            $.each(team.app_ids, function(i, appId) {
                possibleAppIds.push(appId);
            });
        }

        unused_app_ids.push("rogerthat");

        $.each(unused_app_ids, function(i, appId) {
            if (possibleAppIds.indexOf(appId) == -1)
                possibleAppIds.push(appId);
        });

        $.each(possibleAppIds, function(i, appId) {
            var enabled = team && team.app_ids.indexOf(appId) != -1;

            var tmpl = $.tmpl(JS_TEMPLATES.regio_manager_team_apps, {
                app_id : appId
            });

            $('.enabled', tmpl).prop('checked', enabled);

            tbody.append(tmpl);
        });
    };

    var editRegioManager = function(email) {
        var regioManager = email ? regioManagers[email] : null;

        var modal = $('#regio-manager-info').modal('show').data('email', email);

        if (email) {
            $('.edit-email', modal).prop('disabled', true);
            $('.delete-btn', modal).show();
        } else {
            $('.edit-email', modal).prop('disabled', false);
            $('.delete-btn', modal).hide();
        }

        $('.edit-email', modal).val(regioManager ? regioManager.email : '');
        $('.edit-name', modal).val(regioManager ? regioManager.name : '');
        $('.edit-phone', modal).val(regioManager ? regioManager.phone : '');
        $('#show-in-stats', modal).prop('checked', regioManager ? regioManager.show_in_stats : true);
        $('#is-support', modal).prop('checked', regioManager ? regioManager.internal_support : false);
        $('#is-admin', modal).prop('checked', regioManager ? regioManager.admin : false);

        var selectAllRights = function() {
            var self = $(this);
            var readOrWrite = self.hasClass('read-all') ? 'read' : 'write';
            var checkboxes = $('#apps tbody').find('.' + readOrWrite);
            checkboxes.prop('checked', self.is(':checked'));
            checkboxes.trigger('change');
        };

        var rightsChanged = function() {
            var allReadChecked = $('#apps tbody .read').not(':checked').length === 0;
            var allWriteChecked = $('#apps tbody .write').not(':checked').length === 0;
            $('#all-app-rights .read-all').prop('checked', allReadChecked);
            $('#all-app-rights .write-all').prop('checked', allWriteChecked);
        }

        $('#all-app-rights input').change(selectAllRights);
        $(document).on('change', '#apps tbody tr:not(#all-app-rights) input', rightsChanged);

        var renderPossibleApps = function(teamId) {
            var tbody = $('#apps tbody', modal);
            tbody.find('tr:not(#all-app-rights)').remove();
            var possibleAppIds = [];
            if (regioManager) {
                $.each(regioManager.app_ids, function(i, appId) {
                    possibleAppIds.push(appId);
                });
                if (!teamId && regioManager.team_id) {
                    teamId = regioManager.team_id;
                }
                if (teamId) {
                    $.each(teams[teamId].app_ids, function(i, appId) {
                        if (possibleAppIds.indexOf(appId) == -1)
                            possibleAppIds.push(appId);
                    });
                }
            } else if (teamId) {
                $.each(teams[teamId].app_ids, function(i, appId) {
                    if (possibleAppIds.indexOf(appId) == -1)
                        possibleAppIds.push(appId);
                });
            }

            var readCount = 0, writeCount = 0;
            $.each(possibleAppIds, function(i, appId) {
                var write = regioManager && regioManager.app_ids.indexOf(appId) != -1;
                var read = regioManager && (write || regioManager.read_only_app_ids.indexOf(appId) != -1);

                if (read) {
                    readCount++;
                }
                if (write) {
                    writeCount++;
                }

                var tmpl = $.tmpl(JS_TEMPLATES.regio_manager_app_rights, {
                    app_id : appId
                });

                var readCheckbox = $('.read', tmpl).prop('checked', read).change(function() {
                    if (!$(this).is(':checked')) {
                        writeCheckbox.prop('checked', false);
                    }
                });
                var writeCheckbox = $('.write', tmpl).prop('checked', write).change(function() {
                    if ($(this).is(':checked')) {
                        readCheckbox.prop('checked', true);
                    }
                });
                tbody.append(tmpl);
            });

            $('#all-app-rights .read-all').prop('checked', readCount === possibleAppIds.length);
            $('#all-app-rights .write-all').prop('checked', writeCount === possibleAppIds.length);
        };

        renderPossibleApps(null);

        var select = $("#team", modal).empty();
        select.append($('<option></option>').attr('value', "").text("Select team"));
        $.each(teams, function (i, team) {
            select.append($('<option></option>').attr('value', team.id).text(team.name));
        });
        if (regioManager && regioManager.team_id) {
            select.val(regioManager.team_id);
        }
        select.change(function() {
            renderPossibleApps($(this).val());
        });
    };

    var renderRegioManagers = function() {
        var html = $.tmpl(JS_TEMPLATES.regio_manager_list, {
            unassigned_regio_managers : unassignedRegioManagerEmails,
            teams : teams
        });
        $('#regio-managers-container').append(html);

        $('.edit-regio-manager').unbind('click').click(function() {
            editRegioManager($(this).parents('tr').attr('data-regio-manager-email'));
        });

        $('#regio-managers-teams-table .team-edit').unbind('click').click(function() {
            editRegioManagerTeam($(this).attr('data-regio-manager-team-id'));
        });

        $('#regio-managers-table tbody tr').unbind('click').click(function() {
            editRegioManager($(this).attr('data-regio-manager-email'));
        });

        $('#regio-managers-teams-table tbody tr').unbind('click').click(function() {
            editRegioManager($(this).attr('data-regio-manager-email'));
        });
    };

    var loadRegioManagers = function() {
        $('#regio-managers-container').empty();
        showProcessing('Loading...');
        sln.call({
            url : '/internal/shop/rest/regio_manager/list',
            type : 'GET',
            success : function(data) {
                hideProcessing();
                apps = {};
                unused_app_ids = [];
                $.each(data.apps, function(i, app) {
                    apps[app.id] = app;
                    unused_app_ids.push(app.id);
                });
                teams = {};
                $.each(data.regio_manager_teams, function(i, team) {
                    team.color = COLORS[i % COLORS.length];
                    teams[team.id] = team;
                    $.each(team.app_ids, function(j, appId) {
                        var index = unused_app_ids.indexOf(appId)
                        if(index != -1) {
                            unused_app_ids.splice(index, 1);
                        }
                    });

                    $.each(team.regio_managers, function(j, regioManager) {
                        regioManagers[regioManager.email] = regioManager;
                    });
                });


                $.each(data.unassigned_regio_managers, function(i, regioManager) {
                    regioManagers[regioManager.email] = regioManager;
                });
                unassignedRegioManagerEmails = data.unassigned_regio_managers;
                renderRegioManagers();
            },
            error : function() {
                hideProcessing();
                showError('An unknown error occurred. Check with the administrators.');
            }
        });
    };

    $('#regio-manager-team-info').on('shown', function() {
        $('#regiomanagerteam_name', $(this)).focus();
    });

    $('#regio-manager-info').on('shown', function() {
        if (!$(this).data('email')) {
            $('.edit-email', $(this)).focus();
        }
    });

    $('.new-regio-manager-team').click(function() {
        editRegioManagerTeam(null);
    });

    $('.new-regio-manager').click(function() {
        editRegioManager(null);
    });

    $('#regio-manager-info .delete-btn').click(function() {
        var email = $('#regio-manager-info').data('email');

        showConfirmation('Are you sure you want to remove ' + regioManagers[email].name + '?', function() {
            showProcessing('Deleting...');
            sln.call({
                url : '/internal/shop/rest/regio_manager/delete',
                type : 'POST',
                data : {
                    data : JSON.stringify({
                        email : email
                    })
                },
                success : function(data) {
                    hideProcessing();
                    if (!data.success) {
                        showError(data.errormsg);
                        return;
                    }
                    window.location.reload();
                },
                error : function() {
                    hideProcessing();
                    showError('An unknown error occurred. Check with the administrators.');
                }
            });
        });
    });

    $('#regio-manager-team-info .save-btn').click(function() {
        var modal = $('#regio-manager-team-info');
        var team_id = parseInt(modal.data('team_id'));
        var name = $('#regiomanagerteam_name', modal).val();
        var legalEntity = parseInt($('#regiomanagerteam_legal_entity', modal).val());

        if (!name) {
            showError('Name is required');
            return;
        }

        var app_ids = [];
        $.each(apps, function(appId, app) {
            if ($('input.enabled[data-app-id="' + appId + '"]').is(':checked')) {
                app_ids.push(appId);
            }
        });

        var data = {
            team_id: team_id,
            name : name,
            legal_entity_id: legalEntity,
            app_ids : app_ids
        };

        showProcessing('Updating...');
        sln.call({
            url : '/internal/shop/rest/regio_manager_team/put',
            type : 'POST',
            data: data,
            success : function(data) {
                hideProcessing();
                if (!data.success) {
                    showError(data.errormsg);
                    return;
                }
                window.location.reload();
            },
            error : function() {
                hideProcessing();
                showError('An unknown error occurred. Check with the administrators.');
            }
        });
    });


    $('#regio-manager-info .save-btn').click(function() {
        var modal = $('#regio-manager-info');
        var email = $('.edit-email', modal).val();
        var name = $('.edit-name', modal).val();
        var phone = $('.edit-phone', modal).val();
        var showInStats = $('#show-in-stats', modal).prop('checked');
        var isSupport = $('#is-support', modal).prop('checked');
        var isAdmin = $('#is-admin', modal).prop('checked');
        var teamId = $('#team', modal).val();

        if (!email) {
            showError('Email is required');
            return;
        }

        if (!name) {
            showError('Name is required');
            return;
        }

        if (!teamId) {
            showError('Team is required');
            return;
        }

        if (!showInStats) {
            showInStats = false;
        }

        var appRights = [];
        $.each(apps, function(appId, app) {
            var access;
            if ($('input.write[data-app-id="' + appId + '"]').is(':checked')) {
                access = AccessType.FULL;
            } else if ($('input.read[data-app-id="' + appId + '"]').is(':checked')) {
                access = AccessType.READ_ONLY;
            } else {
                access = AccessType.NO;
            }

            appRights.push({
                app_id : appId,
                access : access
            });
        });

        var data = {
            email : email,
            name : name,
            phone: phone,
            app_rights : appRights,
            show_in_stats: showInStats,
            is_support: isSupport,
            team_id: parseInt(teamId),
            admin : isAdmin
        };
        showProcessing('Updating...');
        sln.call({
            url : '/internal/shop/rest/regio_manager/put',
            type : 'POST',
            data : {
                data : JSON.stringify(data)
            },
            success : function(data) {
                hideProcessing();
                if (!data.success) {
                    showError(data.errormsg);
                    return;
                }
                window.location.reload();
            },
            error : function() {
                hideProcessing();
                showError('An unknown error occurred. Check with the administrators.');
            }
        });
    });

    $('#is-support-info').tooltip();
    loadRegioManagers();
});
