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

// Settings module
$(function () {
    var eventsEnabled = true;
    var inboxEmailRemindersEnabled = true;
    var isPublishing = false;

    var TMPL_UPDATES_PENDING = '<div class="alert">'
        + '    <button id="publish_changes" type="button" class="btn btn-warning pull-right">'
        + CommonTranslations.PUBLISH_CHANGES //
        + '    </button>' //
        + '    <button id="try_publish_changes" type="button" class="btn btn-warning pull-right" style="margin-right: 5px;">'
        + CommonTranslations.TRY //
        + '    </button>' //
        + '    <h4>' + CommonTranslations.WARNING + '</h4>' + CommonTranslations["unpersisted-changes"]
        + '</div>';

    var TMPL_USER_ROW = '<tr user_key=${user_key}>'
        + '<td style="width: 75%;"">${email}</td>'
        + '<td><button class="btn btn-danger pull-right" action="delete_user"><i class="fa fa-trash"></i></button></td>'
        + '</tr>';

    var TMPL_SET_EVENTS_VISIBLE = '<div class="btn-group">'
        + '      <button class="btn btn-success" id="eventsVisible">' + CommonTranslations.VISIBLE + '</button>'
        + '      <button class="btn" id="eventsInvisible">&nbsp;</button>' + '</div>';

    var TMPL_SET_INBOX_EMAIL_REMINDERS_ENABLED = '<div class="btn-group">' //
        + '    <button class="btn btn-success" id="inboxEmailRemindersEnabled">' //
        + CommonTranslations.EMAIL_REMINDERS_ENABLED //
        + '    </button>' //
        + '    <button class="btn" id="inboxEmailRemindersDisabled">&nbsp;</button>' //
        + '</div>';

    var INBOX_FORWARDER_TEMPLATE = '{{each forwarders}}' //
        + '<li>' //
        + '{{if ($value.type == "email")}}<i class="icon-envelope"></i> ' //
        + '{{else ($value.type == "mobile")}}<i class="icon-user"></i> ' //
        + '{{/if}}' //
        + '${$value.label} <a fw_type="${$value.type}" user_key="${$value.key}" href="#" action="delete_user_forwarding">'
        + CommonTranslations.DELETE + '</a>' //
        + '</li>' //
        + '{{/each}}';

    var TMPL_MOBILE_INBOX_FORWARDER_INPUT = '<div class="modal hide fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'
        + '    <div class="modal-header">'
        + '        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>'
        + '        <h3 id="myModalLabel">${header}</h3>'
        + '    </div>'
        + '    <div class="modal-body" style="overflow-y: visible;">'
        + '        <input id="mobile_inbox_forwarder" type="text" style="width: 514px" placeholder="${placeholder}..." value="${value}" />'
        + '    </div>'
        + '    <div class="modal-footer">'
        + '        <button action="cancel" class="btn" data-dismiss="modal" aria-hidden="true">${cancelBtn}</button>'
        + '        <button action="submit" class="btn btn-primary">${submitBtn}</button>' //
        + '    </div>' //
        + '</div>';

    init();

    function init() {
        ROUTES.settings = router;
        modules.settings = {publishChanges: publishChanges};
        LocalCache.settings = {};
    }

    function router(urlHash) {
        var page = urlHash[1];
        if (!page) {
            page = 'service-info';
            window.location.hash = '#/' + urlHash[0] + '/' + page;
            return;
        }
        $('#settings').find('li[section=section_' + page + ']').find('a').click();
        var dashboardDisplay = 'none';
        if (page === 'service-info') {
            dashboardDisplay = 'block';
            newDashboardRouter(['settings']);
        } else if (page === 'branding') {
            showSettingsBranding();
        } else if (page === 'app-settings') {
            renderAppSettings();
        } else if (page === 'roles') {
            renderRolesSettings();
        } else if (page === 'broadcast') {
            getBroadcastRssSettings(renderRssSettings);
        } else if (page === 'q-matic') {
            Requests.getQmaticSettings().then(renderQmaticSettings);
        } else if (page === 'jcc-appointments') {
            Requests.getJccSettings().then(renderJccSettings);
        } else if (page === 'paddle') {
            Requests.getPaddleSettings().then(renderPaddleSettings);
        }
        // From sln-new-dashboard.js
        dashboardContainer.style.display = dashboardDisplay;
    }

    function publishChanges() {
        // publish changes to all users
        publishChangesToUsers(null);
    }

    var tryPublishChanges = function () {
        var html = $.tmpl(templates['settings/try_publish_changes'], {});

        var modal = sln.createModal(html, function (modal) {
            $('#app_user_email_input', modal).focus();
        });

        function getUserKeys() {
            var keys = [];
            $('#selected_users > tbody > tr', modal).each(function (i, el) {
                keys.push($(el).attr('user_key'));
            });
            return keys;
        }

        function addUser(userKey) {
            var email = userKey.split(':')[0];
            var userRow = $.tmpl(TMPL_USER_ROW, {
                email: email,
                user_key: userKey
            });

            $('button[action=delete_user]', userRow).click(function () {
                $(this).parent().closest('tr').remove();
            });

            $('#selected_users > tbody', modal).append(userRow);
        }

        if (LocalCache.settings.try_publish_user_keys) {
            $.each(LocalCache.settings.try_publish_user_keys, function (i, userKey) {
                addUser(userKey);
            });
        }

        var publishButton = $('#try_publish', modal);
        var searchInput = $('#app_user_email', modal);
        sln.userSearch(searchInput, function (userKey) {
            var addedKeys = getUserKeys();
            if (addedKeys.indexOf(userKey) === -1) {
                addUser(userKey);
                searchInput.val('');
            }
        });

        publishButton.click(function () {
            var userKeys = getUserKeys(),
                members = [];

            $.each(userKeys, function (i, key) {
                var userKey = key.split(':');
                members.push({
                    member: userKey[0], /* email */
                    app_id: userKey[1]  /* app_id */
                });
            });
            if (!members.length) {
                sln.alert(CommonTranslations.select_1_user_at_least, null, CommonTranslations.ERROR);
                return;
            }

            saveTryPublishUsers(userKeys);
            publishChangesToUsers(members);
            modal.modal('hide');
        });
    };

    function publishChangesToUsers (friends) {
        if (isPublishing) {
            console.debug('Publishing in progress...');
            // do nothing
            return;
        }
        isPublishing = true;
        var args = {};
        if (friends && friends.length) {
            args.friends = friends;
        }
        sln.showProcessing(CommonTranslations.PUBLISHING_DOT_DOT_DOT);
        sln.call({
            url: "/common/settings/publish_changes",
            type: "POST",
            data: args,
            success: function (data) {
                sln.hideProcessing();
                if (data.success && !args.friends) {
                    toggleUpdatesPending(false);
                } else if (!data.success) {
                    sln.alert(sln.htmlize(data.errormsg), null, T('ERROR'));
                }
                isPublishing = false;
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                sln.hideProcessing();
                sln.showAjaxError(XMLHttpRequest, textStatus, errorThrown);
                isPublishing = false;
            }
        });
    }

    var saveTryPublishUsers = function (userKeys) {
        if (userKeys.length) {
            LocalCache.settings.try_publish_user_keys = userKeys;

            sln.call({
                url: '/common/settings/publish_changes/users',
                type: 'POST',
                data: {
                    user_keys: userKeys
                },
                success: function () {
                },
                error: sln.showAjaxError
            });
        }
    };

    var toggleUpdatesPending = function (updatesPending) {
        if (updatesPending) {
            $("#sln-updates-pending-warning").fadeIn('slow');
        } else {
            $("#sln-updates-pending-warning").fadeOut('fast');
        }
        resizeDashboard();  // Defined in sln-new-dashboard.js
    };

    var loadSettings = function () {
        Requests.getSettings({cached: false}).then(function (data) {
            LocalCache.settings = data;
            eventsEnabled = data.events_visible;
            setEventsVisible(eventsEnabled);
            inboxEmailRemindersEnabled = data.inbox_email_reminders;
            setInboxEmailRemindersStatus(inboxEmailRemindersEnabled);
            toggleUpdatesPending(data.updates_pending);

            if (MODULES.indexOf('billing') !== -1 && $('.sln-set-iban input').length) {
                $('.sln-set-iban input').val(data.iban);
                $('.sln-set-bic input').val(data.bic);
            }

            if (data.publish_changes_users) {
                LocalCache.settings.try_publish_user_keys = data.publish_changes_users;
            }
        });
    };

    var channelUpdates = function (data) {
        if (data.type == 'solutions.common.settings.updates_pending') {
            toggleUpdatesPending(data.updatesPending);
        } else if (data.type == 'solutions.common.inbox.new.forwarder.via.scan') {
            inboxLoadForwarders();
        } else if (data.type == 'solutions.common.locations.update') {
            if (!isLoyaltyTablet) {
                if (service_identity != data.si) {
                    window.location.reload();
                }
            }
        } else if (data.type === 'solutions.common.settings.avatar.updated') {
            avatarUpdated(data.avatar_url);
        } else if (data.type === 'solutions.common.settings.logo.updated') {
            logoUpdated(data.logo_url);
        } else if (data.type === 'solution.common.settings.roles.updated') {
            renderRolesSettings();
        }
    };
    /* Bulk invite */

    var testBulkInvites = function () {
        $("#bulkInviteEmailList").empty();
        var emails = extractEmails($('#blukEmails').val());
        var numberOfEmails = 0;
        if (emails != null) {
            $.each(emails, function (index, email) {
                $("#bulkInviteEmailList").append('<li>' + email + '</li>');
                numberOfEmails++;
            });
            $("#bulkInvite").show();
            $('#bulkInviteEmailList li').click(deleteEmailFromList);
        }
        $("#sendBulkEmailInvitations").val(numberOfEmails)
            .text(T('send-invitation-to-x-emails', {amount: numberOfEmails}));
    };

    var deleteEmailFromList = function () {
        $(this).remove();
        var numberOfEmails = $("#sendBulkEmailInvitations").val() - 1;
        $("#sendBulkEmailInvitations").val(numberOfEmails)
            .text(T('send-invitation-to-x-emails', {amount: numberOfEmails}));
    };

    var sendBulkInvites = function () {
        var emails = [];
        $.each($('#bulkInviteEmailList li'), function (index) {
            emails.push($(this).text());
        });
        if (emails.length > 0) {
            sln.showProcessing(CommonTranslations.SENDING_DOT_DOT_DOT);
            $('#sendBulkEmailInvitations').off('click');
            sln.call({
                url: "/common/bulkinvite",
                type: "POST",
                data: {
                    data: JSON.stringify({
                        emails: emails,
                        invitation_message: $('#bulkInvitationMessage').val()
                    })
                },
                success: function (data) {
                    sln.hideProcessing();
                    if (data.success) {
                        $("#bulkInvite").hide();
                        $('#blukEmails').val("");
                        $("#bulkInviteEmailList").empty();
                        $("#sendBulkEmailInvitations").val(0)
                            .click(sendBulkInvites)
                            .text(T('send-invitation-to-x-emails', {amount: 0}));
                        sln.alert(T('All invites were sent successfully'), null, T('Invites sent'), null);
                    }
                },
                error: sln.showAjaxError
            });
        }
    };

    var extractEmails = function (text) {
        var matches = text.match(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+)/gi);
        var emails = [];
        if (matches) {
            emails = matches.sort(sln.caseInsensitiveStringSort).reduce(function (a, b) {
                if (a.indexOf(b) < 0) {
                    a.push(b);
                }
                return a;
            }, []); // this empty array becomes the starting value for a

        }
        return emails;
    };

    function settingTabPress() {
        var settingsElem = $("#settings");
        settingsElem.find('li').removeClass("active");
        var li = $(this).parent().addClass("active");
        settingsElem.find("section").hide();
        settingsElem.find("section#" + li.attr("section")).show();
    }

    function eventsVisible() {
        setEventsVisible(!eventsEnabled);
        saveSettings();
    }

    function eventsInvisible() {
        setEventsVisible(!eventsEnabled);
        saveSettings();
    }

    function setEventsVisible(newEventsEnabled) {
        eventsEnabled = newEventsEnabled;
        if (newEventsEnabled) {
            $('#eventsVisible').addClass("btn-success").text(T('agenda-enabled'));
            $('#eventsInvisible').removeClass("btn-danger").html('&nbsp;');
            $("#topmenu li[menu|='events']").css('display', 'block');
        } else {
            $('#eventsVisible').removeClass("btn-success").html('&nbsp;');
            $('#eventsInvisible').addClass("btn-danger").text(T('agenda-disabled'));
            $("#topmenu li[menu|='events']").css('display', 'none');
        }
    }

    function inboxLoadForwarders() {
        sln.call({
            url: "/common/inbox/forwarders/load",
            type: "GET",
            success: function (data) {
                var inboxForwarders = $("#mobile_inbox_forwarders");
                var html = $.tmpl(INBOX_FORWARDER_TEMPLATE, {
                    forwarders: data
                });
                inboxForwarders.empty().append(html);
                $('#mobile_inbox_forwarders a[action="delete_user_forwarding"]').click(function () {
                    var userKey = $(this).attr("user_key");
                    var fwType = $(this).attr("fw_type");
                    sln.call({
                        url: "/common/inbox/forwarders/delete",
                        type: "POST",
                        data: {
                            data: JSON.stringify({
                                key: userKey,
                                forwarder_type: fwType
                            })
                        },
                        success: function (data) {
                            if (!data.success) {
                                return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                            }
                            inboxLoadForwarders();
                        },
                        error: sln.showAjaxError
                    });
                });
            },
            error: sln.showAjaxError
        });
    }

    var addInboxForwarder = function (key, type) {
        sln.showProcessing(CommonTranslations.LOADING_DOT_DOT_DOT);
        sln.call({
            url: "/common/inbox/forwarders/add",
            type: "POST",
            data: {
                data: JSON.stringify({
                    key: key,
                    forwarder_type: type
                })
            },
            success: function (data) {
                sln.hideProcessing();
                if (!data.success) {
                    return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                }
                inboxLoadForwarders();
            },
            error: sln.showAjaxError
        });
    };

    $("#add_email_inbox_forwarder").click(function () {
        sln.input(function (value) {
            addInboxForwarder(value, 'email');
        }, T('E-mail address'));
    });

    var setInboxEmailRemindersStatus = function (newInboxEmailRemindersStatus) {
        inboxEmailRemindersEnabled = newInboxEmailRemindersStatus;
        if (newInboxEmailRemindersStatus) {
            $('#inboxEmailRemindersEnabled').addClass("btn-success").text(CommonTranslations.EMAIL_REMINDERS_ENABLED);
            $('#inboxEmailRemindersDisabled').removeClass("btn-danger").html('&nbsp;');
        } else {
            $('#inboxEmailRemindersEnabled').removeClass("btn-success").html('&nbsp;');
            $('#inboxEmailRemindersDisabled').addClass("btn-danger").text(CommonTranslations.EMAIL_REMINDERS_DISABLED);
        }
    };

    var inboxEmailReminderEnabled = function () {
        setInboxEmailRemindersStatus(!inboxEmailRemindersEnabled);
        saveSettings();
    };

    var inboxEmailReminderDisabled = function () {
        setInboxEmailRemindersStatus(!inboxEmailRemindersEnabled);
        saveSettings();
    };

    $(".sln-inbox-email-reminders").html(TMPL_SET_INBOX_EMAIL_REMINDERS_ENABLED);
    $('#inboxEmailRemindersEnabled').click(inboxEmailReminderEnabled);
    $('#inboxEmailRemindersDisabled').click(inboxEmailReminderDisabled);

    $("#add_mobile_inbox_forwarder").click(function () {
        var html = $.tmpl(TMPL_MOBILE_INBOX_FORWARDER_INPUT, {
            header: T('add-mobile-inbox-forwarders'),
            cancelBtn: CommonTranslations.CANCEL,
            submitBtn: CommonTranslations.ADD,
            placeholder: T('follower_name_or_email'),
            value: ""
        });
        var modal = sln.createModal(html, function (modal) {
            $('input', modal).focus();
        });
        $('button[action="submit"]', modal).click(function () {
            var key = $(this).attr("user_key");
            addInboxForwarder(key, 'mobile');
            modal.modal('hide');
        });

        $('button[action="submit"]', modal).hide();

        var searchInput = $('#mobile_inbox_forwarder', html);
        sln.userSearch(searchInput, function (user_key) {
            $('button[action="submit"]', modal).attr("user_key", user_key);
            $('button[action="submit"]', modal).show();
        });
    });

    $("#sln-updates-pending-warning").html(TMPL_UPDATES_PENDING).hide();
    $("#sln-updates-pending-warning #publish_changes").click(publishChanges);
    $("#sln-updates-pending-warning #try_publish_changes").click(tryPublishChanges);

    $("#settings").find("> ul > li > a").click(settingTabPress);
    $(".sln-set-events-visibility").html(TMPL_SET_EVENTS_VISIBLE);
    $('#eventsVisible').click(eventsVisible);
    $('#eventsInvisible').click(eventsInvisible);

    $('#newsletter-checkbox').change(function () {
        saveConsent('newsletter', $(this).prop('checked'));
    });

    $('#email_marketing-checkbox').change(function () {
        saveConsent('email_marketing', $(this).prop('checked'));
    });

    // billing tab
    sln.configureDelayedInput($('#sln-set-iban'), saveSettings);
    sln.configureDelayedInput($('#sln-set-bic'), saveSettings);

    loadSettings();
    inboxLoadForwarders();

    sln.registerMsgCallback(channelUpdates);

    // Bulk invite
    sln.configureDelayedInput($('#blukEmails'), testBulkInvites, $("#blukEmailsLabel"), false);
    $('#sendBulkEmailInvitations').click(sendBulkInvites);
    var elemPaddleUrl = $('#paddle-url');
    var elemPaddleMappings = $('#paddle-mappings');
    elemPaddleUrl.change(function () {
        savePaddleSettings();
    });

    var settingsBranding,
        COLOR_REGEX = /^(([A-F0-9]{2}){3})$/i;

    function showSettingsBranding() {
        // Only render when it's not cached in the DOM yet
        if (!settingsBranding) {
            renderSettingsBranding();
        }
    }

    function renderSettingsBranding() {
        $('#branding_settings').html(TMPL_LOADING_SPINNER);
        getSettingsBranding(function (settings) {
            var elemBrandingSettings = $('#branding_settings');
            settingsBranding = settings;
            var html = $.tmpl(templates['settings/settings_branding'], {
                t: CommonTranslations,
                brandingSettings: settingsBranding.branding_settings
            });
            elemBrandingSettings.html(html);
            renderSettingsBrandingPreview();

            // bind events

            var elemColorScheme = $("#color_scheme"),
                elemShowName = $('#show_name'),
                elemInputShowAvatar = $('#show_avatar');

            elemColorScheme.change(function () {
                settingsBranding.branding_settings.color_scheme = elemColorScheme.val();
                recolorPreviewFrame();
            });

            elemShowName.change(function () {
                var showName = this.checked;
                settingsBranding.branding_settings.show_identity_name = showName;
                $("#preview_frame").contents().find('body').toggleClass('show_identity_name', showName);
                resizeBranding();
            });

            elemInputShowAvatar.change(function () {
                var showAvatar = this.checked;
                settingsBranding.branding_settings.show_avatar = showAvatar;
                $("#preview_frame").contents().find('body').toggleClass('show_avatar', showAvatar);
                resizeBranding();
            });

            $('#save_button', elemBrandingSettings).click(function () {
                var $this = $(this);
                $this.text(CommonTranslations.SAVING_DOT_DOT_DOT);
                sln.call({
                    url: "/common/settings/branding",
                    type: "POST",
                    data: {
                        branding_settings: settingsBranding.branding_settings
                    },
                    success: function (data) {
                        $this.text(CommonTranslations.SAVE);
                        if (!data.success) {
                            return sln.alert(data.errormsg);
                        }
                    },
                    error: function () {
                        $this.text(CommonTranslations.ERROR);
                        setTimeout(function () {
                            $this.text(CommonTranslations.SAVE);
                        }, 10000);
                        sln.showAjaxError();
                    }
                });
            });

            $('.color-picker', elemBrandingSettings).on('input', colorPickerChanged);
            $('.color', elemBrandingSettings).on('input', colorChanged);
            sln.fixColorPicker($('#text_color'), $("#text_color_picker"), fixedColourPickerChanged);
            sln.fixColorPicker($('#background_color'), $("#background_color_picker"), fixedColourPickerChanged);
            sln.fixColorPicker($('#menu_item_color'), $("#menu_item_color_picker"), fixedColourPickerChanged);

            function colorPickerChanged() {
                var pickerInput = $(this);
                var pickerId = pickerInput.attr('id').replace('_picker', '');
                var colour = pickerInput.val().substring(1);
                var colourValid = colour && COLOR_REGEX.test(colour);
                var colourPicker = $('#' + pickerId);
                colourPicker.parent().parent().toggleClass('error', !colourValid);
                if (colourValid) {
                    settingsBranding.branding_settings[pickerId] = colour;
                    colourPicker.val(colour);
                    recolorPreviewFrame();
                }
            }

            function colorChanged() {
                var colorInput = $(this);
                var colour = colorInput.val().replace('#', '');
                var colorInputId = colorInput.attr('id');
                var colourValid = colour && COLOR_REGEX.test(colour);
                colorInput.parent().parent().toggleClass('error', !colourValid);
                if (colourValid) {
                    settingsBranding.branding_settings[colorInputId] = colour;
                    $('#' + colorInputId + '_picker').val('#' + colour);
                    recolorPreviewFrame();
                }
            }

            function fixedColourPickerChanged() {
                var colorInput = $(this);
                var colorInputText = colorInput.find('input[type=text]');
                var colour = colorInputText.val().replace('#', '');
                var colourValid = colour && COLOR_REGEX.test(colour);
                colorInput.parent().parent().toggleClass('error', !colourValid);
                if (colourValid) {
                    settingsBranding.branding_settings[colorInputText.attr('id')] = colour;
                    recolorPreviewFrame();
                }
            }
        });
    }

    function getSettingsBranding(callback) {
        if (!settingsBranding) {
            loadSettingsBranding(callback);
        } else {
            callback(settingsBranding);
        }
    }

    function loadSettingsBranding(callback) {
        sln.call({
            url: "/common/settings/branding_and_menu",
            type: "GET",
            success: callback
        });
    }

    var previewRenderingTimeout;

    function recolorPreviewFrame() {
        var css = {
            'background-color': '#' + settingsBranding.branding_settings.background_color,
            'color': '#' + settingsBranding.branding_settings.text_color,
            'overflow': 'hidden'
        };
        var canvas = $('#canvas').css('background-color', '#' + settingsBranding.branding_settings.background_color);
        $('#preview_frame').contents().find('body').css(css);

        if (previewRenderingTimeout) {
            clearTimeout(previewRenderingTimeout);
        }
        previewRenderingTimeout = setTimeout(function () {
            $('.service-menu-preview').find('td')
                .removeClass().addClass('rt-cs-' + settingsBranding.branding_settings.color_scheme)
                .find('span').css('background-color', '#' + settingsBranding.branding_settings.menu_item_color)
                .find('i.fa').css('color', '#' + settingsBranding.branding_settings.background_color);
            canvas.find('td').find('img').each(function () {
                var $this = $(this);
                var src = $this.attr('src');
                $this.attr('src', src.split('=')[0] + '=' + settingsBranding.branding_settings.menu_item_color);
            });
        }, 300);
    }

    function renderSettingsBrandingPreview() {
        var html = $.tmpl(templates['settings/settings_branding_preview'], {
            t: CommonTranslations,
            brandingSettings: settingsBranding.branding_settings,
            menuItems: settingsBranding.menu_item_rows
        });
        $('#branding_settings_preview').html(html);


        // bind events
        var elemIframe = $('#preview_frame').load(function () {
            var contents = elemIframe.contents();
            contents.find('body').toggleClass('show_identity_name', settingsBranding.branding_settings.show_identity_name);
            contents.find('body').toggleClass('show_avatar', settingsBranding.branding_settings.show_avatar);
            var avatarUrl = settingsBranding.branding_settings.avatar_url || '/static/images/avatar-placeholder.jpg';
            var logoUrl = settingsBranding.branding_settings.logo_url || '/static/images/logo-placeholder.jpg';
            contents.find('#avatar').css('background-image', 'url(' + avatarUrl + ')');
            contents.find('#logo').attr('src', logoUrl);
            resizeBranding();
            recolorPreviewFrame();
            setTimeout(resizeBranding, 200);
            setTimeout(resizeBranding, 2000);
            setTimeout(resizeBranding, 5000);
        });
    }

    function resizeBranding() {
        var elemIFrame = $("#preview_frame").height(50);
        var iframeDocument = elemIFrame.contents().first();
        if (iframeDocument && iframeDocument.length) {
            var height = iframeDocument.height();
            elemIFrame.height(height);
        }
    }

    function saveSettings() {
        var data = {
            events_visible: eventsEnabled,
            inbox_email_reminders: inboxEmailRemindersEnabled,
            iban: $('#sln-set-iban').val(),
            bic: $('#sln-set-bic').val()
        };
        return Requests.saveSettings(data).then(function (settings) {
        });
    }

    function saveConsent(consent_type, enabled) {
        sln.call({
            url: "/common/settings/consent",
            type: "POST",
            data: {
                consent_type: consent_type,
                enabled: enabled
            },
            success: function (data) {
                if (!data.success) {
                    sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                }
            }
        });
    }

    function getBroadcastRssSettings(callback) {
        if (LocalCache.broadcastRssSettings) {
            callback(LocalCache.broadcastRssSettings);
        } else {
            sln.call({
                url: "/common/broadcast/rss",
                type: "GET",
                success: function (data) {
                    LocalCache.broadcastRssSettings = data;
                    callback(data);
                }
            });
        }
    }

    function addBroadcastNewsPublisher() {
        $('li[section=section_roles]').find('a').click();
        renderRolesSettings();
        // show the add roles dialog with only news publisher option
        addRoles(false, false, true);
    }

    $('#sln-set-broadcast-add-rss').click(addRssUrl);
    // add broadcast news publisher
    $('#broadcast_add_news_publisher').click(addBroadcastNewsPublisher);

    function addRssUrl() {
        var html = $.tmpl(templates.broadcast_rss_add_scraper, {
            header: CommonTranslations.ADD,
            cancelBtn: CommonTranslations.CANCEL,
            submitBtn: CommonTranslations.SAVE,
            CommonTranslations: CommonTranslations
        });

        var modal = sln.createModal(html);
        $('button[action="submit"]', modal).click(function () {
            var newRSSScraper = {
                url: $("#rss-scraper-url").val(),
                group_type: $("#rss-scraper-group_type").val(),
                app_ids: $("#rss-scraper-app_ids").val().split("\n")
            };

            getBroadcastRssSettings(function (settings) {
                var newSettings = Object.assign({}, settings, {scrapers: settings.scrapers.concat([newRSSScraper])});
                saveRssSettings(newSettings);
                modal.modal('hide');
            });
        });
    }

    function renderRssSettings(settings) {
        var htmlElement = $('#sln-set-broadcast-rss-urls');
        var html = $.tmpl(templates.broadcast_rss_settings, {
            notify: settings.notify,
            scrapers: settings.scrapers,
            T: T,
        });
        htmlElement.html(html);
        htmlElement.find('button[action="deleteRssUrl"]').click(deleteRssUrl);
        var notifyCheckbox = htmlElement.find('#send-rss-notifications');
        notifyCheckbox.change(function () {
            getBroadcastRssSettings(function (settings) {
                settings.notify = notifyCheckbox.prop('checked');
                saveRssSettings(settings);
            });
        });
    }

    function deleteRssUrl() {
        var url = $(this).attr('rss_url');
        getBroadcastRssSettings(function (settings) {
            settings.scrapers = settings.scrapers.filter(function (scraper) {
                return scraper.url !== url;
            });
            saveRssSettings(settings);
        });
    }

    function saveRssSettings(settings) {
        Requests.saveRssSettings(settings, {showError: false}).then(function (data) {
            LocalCache.broadcastRssSettings = data;
            renderRssSettings(data);
        }).catch(function (error) {
            if (error.responseJSON) {
                if (error.responseJSON.error === 'invalid_rss_links') {
                    sln.alert(T('errors.invalid_rss_link', {url: error.responseJSON.data.invalid_links[0]}));
                } else {
                    sln.showAjaxError();
                }
            } else {
                sln.showAjaxError();
            }
        });
    }

    function avatarUpdated(url) {
        // Update in branding preview
        $('#preview_frame').contents().find('#avatar').css('background-image', 'url(' + url + ')');
    }

    function logoUpdated(url) {
        // Update in branding preview
        $('#preview_frame').contents().find('#logo').attr('src', url);
    }

    function saveAppSettings() {
        var birthdayMessageEnabled = $('#birthday_message_enabled').prop('checked'),
            birthdayMessage = $('#birthday_message').val();
        var data = {
            settings: {
                birthday_message_enabled: birthdayMessageEnabled,
                birthday_message: birthdayMessage
            }
        };
        Requests.saveAppSettings(data).then(renderAppSettings);
    }

    function renderAppSettings() {
        Requests.getAppSettings().then(render);

        function render(appSettings) {
            var html = $.tmpl(templates['settings/app_settings'], {
                settings: appSettings,
                sln: sln
            });
            $('#section_app-settings').html(html);
            $('#birthday_message_enabled').change(saveAppSettings);
            sln.configureDelayedInput($('#birthday_message'), saveAppSettings);
        }
    }

    function getAllUserRoles(callback) {
        sln.call({
            url: '/common/users/roles/load',
            success: callback,
            error: sln.showAjaxError
        });
    }

    function addRoles(inboxEnabled, agendaEnabled, broadcastEnabled) {
        // get the available calendars first
        if (agendaEnabled) {
            sln.call({
                url: '/common/calendar/load',
                success: showAddRolesModal,
                error: sln.showAjaxError
            });
        } else {
            showAddRolesModal([]);
        }

        function showAddRolesModal(calendars) {
            var html = $.tmpl(templates['settings/app_user_add_roles'], {
                calendars: calendars,
                inbox_enabled: inboxEnabled,
                broadcast_enabled: broadcastEnabled
            });

            var modal = sln.createModal(html, function (modal) {
                $('#app_user_email_input', modal).focus();
            });

            // show inbox forwarder type if inbox forwarder
            $('#is_inbox_forwarder', modal).change(function () {
                if ($(this).is(':checked')) {
                    $('#forwarder_type_selection', modal).show();
                } else {
                    $('#forwarder_type_selection', modal).hide();
                }
            });

            // search the existing users
            // just like events add admin or add inbox forwarer
            var searchInput = $('#app_user_email_input', modal);
            sln.userSearch(searchInput,
                function (user_key) {
                    $('button[action="submit"]', modal).attr("user_key", user_key);
                },
                function (query) {
                    $('button[action="submit"]', modal).attr("user_key", "");
                });

            $('button[action="submit"]', modal).click(function () {
                var userKey = $(this).attr('user_key');
                var inboxForwarder, newsPublisher;
                inboxForwarder = $('#is_inbox_forwarder').is(':checked');
                newsPublisher = $('#is_news_publisher').is(':checked');
                var forwarderType = $('input[name=forwarder_type]:checked').attr('forwarder_type');
                // user selected no roles
                if (!(inboxForwarder || newsPublisher)) {
                    sln.alert(CommonTranslations.roles_please_select_one_role_at_least, null, CommonTranslations.ERROR);
                    return;
                }

                // if the user key is not set, then it's an email address
                // this email address can be for a non-existing user
                // so he/she cannot has any role other than email inbox forwarder
                if (!userKey) {
                    if ((inboxForwarder && (forwarderType === 'mobile')) || newsPublisher) {
                        // we need a valid user (not just an email) in these cases
                        sln.alert(T('roles_please_provide_user'), null, CommonTranslations.ERROR);
                        return;
                    }
                    // this is an email inbox forwarder
                    // so check the input email address
                    userKey = $('#app_user_email_input').val();
                    if (!userKey) {
                        sln.alert(T('roles_please_provide_email'), null, CommonTranslations.ERROR);
                        return;
                    }
                }
                // only add a forwarder type per time
                // to disable other roles for any email that doesn't exist as a user
                var forwarderTypes = [forwarderType];
                sln.call({
                    url: '/common/users/roles/add',
                    method: 'post',
                    showProcessing: true,
                    data: {
                        key: userKey,
                        user_roles: {
                            inbox_forwarder: inboxForwarder,
                            news_publisher: newsPublisher,
                            forwarder_types: forwarderTypes,
                        }
                    },
                    success: function (data) {
                        if (data.success) {
                            modal.modal('hide');
                            renderRolesSettings();
                        } else {
                            sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                        }
                    },
                    error: sln.showAjaxError
                });
            });
        }
    }

    function renderRolesSettings() {
        // check if inbox, agenda and broadcast modules are enabled
        // cannot figure out another way to check it from the client side!
        var inboxEnabled = $('#section_inbox').length > 0;
        var agendaEnabled = $('#section_agenda').length > 0;
        var broadcastEnabled = $('#section_broadcast').length > 0;

        var container = $('#section_roles').find('.user-roles');
        container.html(TMPL_LOADING_SPINNER);

        getAllUserRoles(render);

        function render(data) {
            var html = $.tmpl(templates['settings/app_user_roles'], {
                T: T,
                roles: data,
                inbox_enabled: inboxEnabled,
                broadcast_enabled: broadcastEnabled,
            });

            $('#add_user_roles', html).click(function () {
                addRoles(inboxEnabled, agendaEnabled, broadcastEnabled);
            });

            $('button[action=delete_roles]', html).click(deleteRoles);

            function deleteRoles() {
                var key = $(this).attr('user_key');
                var email = key.split(':')[0];
                var row = $('tr[user_key="' + key + '"]', html);
                var forwarderTypes = $('input[name=inbox]', row).attr('forwarder_types');
                var calendarIds = $('input[name=calendar]', row).attr('calendar_ids');

                if (!forwarderTypes) {
                    forwarderTypes = [];
                } else {
                    forwarderTypes = forwarderTypes.split(',');
                }

                if (!calendarIds) {
                    calendarIds = [];
                } else {
                    calendarIds = calendarIds.split(',').map(function (i) {
                        return parseInt(i);
                    });
                }

                var confirmMessage = T('roles_delete_confirmation', {email: email});
                sln.confirm(confirmMessage, doDelete, null, null, null, null);

                function doDelete() {
                    sln.call({
                        url: '/common/users/roles/delete',
                        showProcessing: true,
                        method: 'post',
                        data: {
                            key: key,
                            forwarder_types: forwarderTypes,
                            calendar_ids: calendarIds
                        },
                        success: function (data) {
                            if (data.success) {
                                renderRolesSettings();
                            } else {
                                sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                            }
                        },
                        error: sln.showAjaxError
                    });
                }


            }

            loadAdmins();

            function loadAdmins() {
                $('#section_roles').find('.admin-logins').html(TMPL_LOADING_SPINNER);
                sln.call({
                    url: '/common/users/admins',
                    type: 'get',
                    success: renderAdminSettings,
                    error: sln.showAjaxError
                });
            }

            function renderAdminSettings(adminEmails) {
                LocalCache.settings.service_admins = adminEmails;

                var container = $('#section_roles').find('.admin-logins');

                var html = $.tmpl(templates['settings/app_user_admins'], {
                    admins: adminEmails,
                });

                container.html(html);
                container.find('#add_admin').click(addAdmin);
            }

            function addAdmin() {
                function add(email) {
                    var serviceEmails = LocalCache.settings.service_admins;
                    if (serviceEmails && serviceEmails.length) {
                        if (serviceEmails.indexOf(email) !== -1) {
                            sln.alert(T('x_already_exists', {x: email}));
                            return;
                        }
                    }

                    sln.call({
                        url: '/common/users/admins',
                        type: 'post',
                        showProcessing: true,
                        data: {
                            user_email: email,
                        },
                        success: function (result) {
                            if (result.success) {
                                serviceEmails.push(email);
                                renderAdminSettings(serviceEmails);
                            } else {
                                sln.alert(result.errormsg, null, CommonTranslations.ERROR);
                            }
                        },
                        error: sln.showAjaxError
                    });
                }

                sln.input(add, T('E-mail address'), null, T('E-mail address'), '', 'email');
            }

            $('#app_users_count', html).text(data.length);
            container.html(html);
        }
    }

    function savePaddleSettings(data) {
        if (data) {
        } else {
            var url = elemPaddleUrl.val();
            if (url) {
                url = url.trim();
            }
            data = {base_url: url, mapping: []};
        }
        return Requests.savePaddleSettings(data).then(renderPaddleSettings);
    }

    function renderPaddleSettings(data) {
        elemPaddleUrl.val(data.settings.base_url);
        var templateVars = {
            services: data.services,
            mappings: data.settings.mapping
        };
        elemPaddleMappings.html($.tmpl(templates['settings/paddle'], templateVars));
        $('.paddle-service-select').change(function () {
            var select = $(this);
            var serviceUser = select.val();
            var paddleId = select.closest('tr').data('paddleId').toString();
            for (var i = 0, a = data.settings.mapping; i < a.length; i++) {
                var mapping = a[i];
                if (mapping.paddle_id === paddleId) {
                    mapping.service_email = serviceUser;
                    break;
                }
            }
            savePaddleSettings(data.settings).then(function () {
                if (data.settings.base_url) {
                    loadSettings();
                }
            });
        });
    }

    function renderQmaticSettings(settings) {
        var url = $('#qmatic_url');
        var authToken = $('#qmatic_auth_token');
        var saveButton = $('#btn_save_qmatic_settings');
        url.val(settings.url);
        authToken.val(settings.auth_token);
        saveButton.prop('disabled', false);
        saveButton.click(function () {
            if (saveButton.prop('disabled')) {
                return;
            }
            saveButton.prop('disabled', true);
            var data = {
                url: url.val(),
                auth_token: authToken.val(),
            };
            Requests.saveQmaticSettings(data, {showError: false})
                .then(function () {
                    saveButton.prop('disabled', false);
                })
                .catch(function (err) {
                    saveButton.prop('disabled', false);
                    if (err.responseJSON.error) {
                        saveButton.prop('disabled', false);
                        if (err.responseJSON.error === 'errors.invalid_qmatic_credentials') {
                            sln.alert(T('errors.invalid_qmatic_credentials'));
                        } else {
                            sln.alert(err.responseJSON.error);
                        }
                    } else {
                        sln.showAjaxError();
                    }
                });
        });
    }

    function renderJccSettings(settings) {
        var url = $('#jcc_url');
        var saveButton = $('#btn_save_jcc_settings');
        url.val(settings.url);
        saveButton.prop('disabled', false);
        saveButton.click(function () {
            if (saveButton.prop('disabled')) {
                return;
            }
            saveButton.prop('disabled', true);
            var data = {
                url: url.val(),
            };
            Requests.saveJccSettings(data, {showError: false})
                .then(function () {
                    saveButton.prop('disabled', false);
                })
                .catch(function (err) {
                    saveButton.prop('disabled', false);
                    if (err.responseJSON.error) {
                        saveButton.prop('disabled', false);
                        sln.alert(err.responseJSON.error);
                    } else {
                        sln.showAjaxError();
                    }
                });
        });
    }
});
