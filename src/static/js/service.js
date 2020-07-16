/*
 * Copyright 2020 Green Valley Belgium NV
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
 * @@license_version:1.7@@
 */

var serviceScript = function () {
    var container = "#servicePanelContainer";
    var container_name = "servicePanelContainer";
    var lj = mctracker.getLocaljQuery(container);
    var apiKeyToDeleteDetails = null;
    var callbackConfigNameToDeleteDetails = null;

    var ak_template = '<li><span class="mcdata">${name}</span><br><span style="font-family: monospace;">${key}</span><br>Generated on ${date} <a class="action-link">Delete</a></li>';
    var ai_template = '{{each actions}}<li class="mcwarning">${$value}</li>{{/each}}';
    var cc_template = '<li><span class="mcdata">${name}</span><br><span style="font-family: monospace;">${uri}</span><br>Created on ${date} - <a class="action-link cc-test">Test</a> - <a class="action-link cc-edit">Edit</a> - <a class="action-link cc-delete">Delete</a></li>';

    var applyJQueryInUI = function () {
        lj("#apiKeysContainer").panel({
            collapsible:false
        });
        lj("#callbackRpcDetailsContainer").panel({
            collapsible:false
        });
        lj("#serviceStatusContainer").panel({
            collapsible:false
        });
        lj("#interactiveLoggingDialog").dialog({
            autoOpen: false,
            modal: false,
            width: '400px',
            title: "Test callback response logs"
        }).attr('dialog', container);
        lj("#serviceAdministratorsContainer").panel({
            collapsible: false
        });
        lj("#importExportContainer").panel({
            collapsible: false
        });
        lj('#importForm').submit(function(e){
            console.log(e);
        });
        lj('#exportServiceData').click(function(e){
            mctracker.call({
                url: "/mobi/service/export",
                hideProcessing: true,
                success: function (data) {
                    checkExport(data.download_url);
                },
                error: function (data) {
                    var message = 'An unknown error occured';
                    try {
                        message = JSON.parse(data.responseText).message;
                    } catch (e) {
                        console.error(e);
                    }
                    mctracker.alert(message);
                }
            });
        });

        function checkExport(downloadUrl) {
            mctracker.showProcessing();
            var interval = setInterval(function () {
                mctracker.call({
                    url: downloadUrl, method: 'HEAD', success: function () {
                        clearInterval(interval);
                        mctracker.hideProcessing();
                        mctracker.alert('Export is ready: <a download href="' + downloadUrl + '">Download</a>', null, null, null, true);
                    }, error: function (response) {
                        if (response.status !== 404) {
                            clearInterval(interval);
                            mctracker.alert(response.responseText);
                        }
                    }
                });
            }, 2000);
        }
        lj("#addAdministratorDialog #email").autocomplete({
            source: function (request, response) {
                mctracker.call({
                    url: "/mobi/rest/service/search_users",
                    hideProcessing: true,
                    data: {
                        admin: true,
                        app_id: "rogerthat",
                        term: request.term
                    },
                    success: function (data, textStatus, XMLHttpRequest) {
                        result = [];
                        $.each(data, function (i, user) {
                          result.push({label: user.name + '<'+ user.email+'>', value: user.email});
                        });
                        response(result);
                    },
                    error: function () {
                        response([]);
                    }
                })
            },
            minLength: 3,
            select: function( event, ui ) {
                $(this).val(ui.item.value);
            }
        });
        mctracker.call({
           url: '/mobi/rest/service/admin/roles',
           success: function  (data, textStatus, XMLHttpRequest) {
               var templ = "{{each roles}}<option value=\"${$value}\">${$value}</option>{{/each}}";
               lj("#role", "dc").append( $.tmpl(templ, {roles:data}) );
           }
        });
        lj("#addAdministratorDialog").dialog({
            autoOpen: false,
            modal: true,
            width: '400px',
            title: "Add administrator",
            open: function () {
                lj("#email", "dc").val('').focus();
                lj("#role", "dc").val('');
            },
            buttons: {
                'Grant': function () {
                    var email = $.trim(lj("#email", "dc").val());
                    if (!email) {
                        lj("#email_required", "dc").show();
                        lj("#email", "dc").focus();
                        return;
                    }
                    var role = lj("#role", "dc").val();
                    mctracker.call({
                        url: '/mobi/rest/service/admin/roles/grant',
                        type: 'POST',
                        data: {
                            data: JSON.stringify({
                                user_email: email,
                                role: role,
                                identity: '+default+'
                            })
                        },
                        success: function  (data, textStatus, XMLHttpRequest) {
                            if (!data.success) {
                                mctracker.alert(data.errormsg);
                                return;
                            }
                            lj("#addAdministratorDialog", "d").dialog('close');
                            mctracker.alert("Administrator added successfully.");
                        }
                    });
                },
                'Cancel': function () {
                    lj("#addAdministratorDialog", "d").dialog('close');
                }
            }
        }).attr('dialog', container);
        lj("#getNameForAPIKeyDialog").dialog({
            autoOpen: false,
            modal: true,
            width: '400px',
            title: "Generate new api key",
            open: function () {
                lj("#keyName", "dc").focus();
            },
            buttons: {
                'Generate': function () {
                    var name = $.trim(lj("#keyName", "dc").val());
                    if (!name) {
                        lj("#name_required", "dc").show();
                        lj("#keyName", "dc").focus();
                        return;
                    }
                    mctracker.call({
                        url: '/mobi/rest/service/generate_api_key',
                        type: 'POST',
                        data: {
                            data: JSON.stringify({
                                name: name
                            })
                        },
                        success: function  (data, textStatus, XMLHttpRequest) {
                            lj("#getNameForAPIKeyDialog", "d").dialog('close');
                            configuration2Screen(data);
                        }
                    });
                },
                'Cancel': function () {
                    lj("#getNameForAPIKeyDialog", "d").dialog('close');
                }
            }
        }).attr('dialog', container);

        lj("#deleteAPIKey").dialog({
            autoOpen: false,
            modal: true,
            width: '400px',
            title: "Delete api key",
            buttons: {
                'Delete': function () {
                    mctracker.call({
                        url: '/mobi/rest/service/delete_api_key',
                        type: 'POST',
                        data: {
                            data: JSON.stringify({
                                key: apiKeyToDeleteDetails.key
                            })
                        },
                        success: function  (data, textStatus, XMLHttpRequest) {
                            lj("#deleteAPIKey", "d").dialog('close');
                            configuration2Screen(data);
                        },
                        error: function (data, textStatus, XMLHttpRequest) {
                            mctracker.showAjaxError(XMLHttpRequest, textStatus, data);
                        }
                    });
                },
                'Cancel': function () {    lj("#deleteAPIKey", "d").dialog('close'); }
            }
        }).attr('dialog', container);

        lj("#addCallbackConfigDialog").dialog({
            autoOpen: false,
            modal: true,
            width: '400px',
            title: "Create new callback configuration",
            open: function () {
                lj("#addCallbackConfigDialog_name", "dc").val("");
                lj("#addCallbackConfigDialog_nameRequired", "dc").hide();
                lj("#addCallbackConfigDialog_regex", "dc").val("");
                lj("#addCallbackConfigDialog_regexRequired", "dc").hide();

                lj("#addCallbackConfigDialog_httpCallBackURI", "dc").val("");
                lj("#addCallbackConfigDialog_httpCallBackURIRequired", "dc").hide();

                lj("#addCallbackConfigDialog_customHeaders", "dc").val("");
                lj("#addCallbackConfigDialog_name", "dc").focus();
            },
            buttons: {
                'Create': function () {
                    lj("#addCallbackConfigDialog_nameRequired", "dc").hide();
                    lj("#addCallbackConfigDialog_regexRequired", "dc").hide();
                    lj("#addCallbackConfigDialog_httpCallBackURIRequired", "dc").hide();

                    var name = $.trim(lj("#addCallbackConfigDialog_name", "dc").val());
                    if (!name) {
                        lj("#addCallbackConfigDialog_nameRequired", "dc").show();
                        lj("#addCallbackConfigDialog_name", "dc").focus();
                        return;
                    }
                    var httpURI = null;
                    httpURI = lj("#addCallbackConfigDialog_httpCallBackURI", "dc").val();
                    if (!httpURI) {
                        lj("#addCallbackConfigDialog_httpCallBackURIRequired", "dc").show();
                        lj("#addCallbackConfigDialog_httpCallBackURI", "dc").focus();
                        return;
                    }

                    var regexes = [];
                    var callbacks = -1;
                    if (lj("#addCallbackConfigDialog_sectionRegex", "dc").is(":visible")) {
                    	var regex = $.trim(lj("#addCallbackConfigDialog_regex", "dc").val());
                        if (!regex) {
                            lj("#addCallbackConfigDialog_regexRequired", "dc").show();
                            lj("#addCallbackConfigDialog_regex", "dc").focus();
                            return;
                        }
                        regexes.push(regex);
                    }
                    if (lj("#addCallbackConfigDialog_sectionCallback", "dc").is(":visible")) {
                    	callbacks = 0;
                    	lj("#addCallbackConfigDialog_sectionCallback input[type=checkbox]", "dc").each(function () {
                    		if ($(this).attr('checked')) {
                    			var code = $(this).attr('code');
                                if (code) {
                                    code = new Number(code);
                                    callbacks += code;
                                }
                    		}
                        });
                    }
                    var customHeaders = lj("#addCallbackConfigDialog_customHeaders", "dc").val();

                    mctracker.call({
                        url: '/mobi/rest/service/create_callback_configuration',
                        type: 'POST',
                        data: {
                            data: JSON.stringify({
                                name: name,
                                httpURI: httpURI,
                                regexes: regexes,
                                callbacks: callbacks,
                                custom_headers: customHeaders
                            })
                        },
                        success: function  (data, textStatus, XMLHttpRequest) {
                            lj("#addCallbackConfigDialog", "d").dialog('close');
                            configuration2Screen(data);
                        },
                        error: function (data, textStatus, XMLHttpRequest) {
                            mctracker.showAjaxError(XMLHttpRequest, textStatus, data);
                        }
                    });
                },
                'Cancel': function () {
                    lj("#addCallbackConfigDialog", "d").dialog('close');
                }
            }
        }).attr('dialog', container);

        lj("#deleteCallbackConfigDialog").dialog({
            autoOpen: false,
            modal: true,
            width: '400px',
            title: "Delete callback configuration",
            buttons: {
                'Delete': function () {
                    mctracker.call({
                        url: '/mobi/rest/service/delete_callback_configuration',
                        type: 'POST',
                        data: {
                            data: JSON.stringify({
                                name: callbackConfigNameToDeleteDetails.name
                            })
                        },
                        success: function  (data, textStatus, XMLHttpRequest) {
                            lj("#deleteCallbackConfigDialog", "d").dialog('close');
                            configuration2Screen(data);
                        },
                        error: function (data, textStatus, XMLHttpRequest) {
                            mctracker.showAjaxError(XMLHttpRequest, textStatus, data);
                        }
                    });
                },
                'Cancel': function () {    lj("#deleteCallbackConfigDialog", "d").dialog('close'); }
            }
        }).attr('dialog', container);

        lj("#generateKey").button().click(function () {
            lj("#name_required", "dc").hide();
            lj("#keyName", "dc").val("");
            lj("#getNameForAPIKeyDialog", "d").dialog('open');
        });
        lj("#saveConfiguration").button().click(saveConfiguration);
        lj("#testConfiguration").button().click(testConfiguration);
        lj("#addAdministrator").button().click(addAdministrator);
        $("input", lj("#callBackMethods")).change(enabledSaveConfiguration).keypress(enabledSaveConfiguration);
        lj("#httpCallBackURI").change(showHTTPWarning).keypress(showHTTPWarning);
        lj("#generateSIK").click(regenerateSIK);
        lj("#chkEnabled").change(toggleEnabled);
        lj("*").attr('disabled', true).not(lj("#noAPIKeys")).fadeTo(0, 0.6);

        $("#svcUpdatesPending").click(publishPendingChanges);
    };

    var addAdministrator = function () {
        lj("#addAdministratorDialog", "d").dialog('open');
    };

    var toggleEnabled = function () {
        mctracker.call({
            url: '/mobi/rest/service/' + (lj("#chkEnabled").prop("checked") ? 'enable' : 'disable'),
            type: 'POST',
            data: {
                data: JSON.stringify({})
            },
            success: function  (data, textStatus, XMLHttpRequest) {
                configuration2Screen(data);
            },
            error: function (data, textStatus, XMLHttpRequest) {
                mctracker.showAjaxError(XMLHttpRequest, textStatus, data);
            }
        });
    };

    var showHTTPWarning = function () {
        var uri = lj("#httpCallBackURI").val();
        if ( uri.length > 5 && uri.substring(0, 5) == "http:")
            lj("#httpCallBackURIWarning").text("* Using plain http for callbacks is insecure as it sends your service identification key unencrypted over the internet.");
        else
            lj("#httpCallBackURIWarning").text("");
    };

    var enabledSaveConfiguration = function () {
        lj("#saveConfiguration").removeAttr('disabled').fadeTo('slow', 1);
    };

    var regenerateSIK = function () {
        mctracker.call({
            url: '/mobi/rest/service/regenerate_sik',
            type: 'POST',
            data: {
                data: JSON.stringify({})
            },
            success: function  (data, textStatus, XMLHttpRequest) {
                configuration2Screen(data);
            },
            error: function (data, textStatus, XMLHttpRequest) {
                mctracker.showAjaxError(XMLHttpRequest, textStatus, data);
            }
        });
    };

    var testConfiguration = function () {
        var textarea = lj("#logWindow", "dc");
        textarea.val("Launching testcallback...\n");
        lj("#interactiveLoggingDialog", "d").dialog('open');
        mctracker.call({
            url: '/mobi/rest/service/perform_test_callback',
            type: 'POST',
            data: {
                data: JSON.stringify({})
            },
            success: function  (data, textStatus, XMLHttpRequest) {
                textarea.val(textarea.val()+"Succesfully launched test callback, result will be posted.\n");
            },
            error: function (data, textStatus, XMLHttpRequest) {
                mctracker.showAjaxError(XMLHttpRequest, textStatus, data);
            }
        });
    };

    var saveConfiguration = function() {
        // Validate configuration
        lj("#validationError").text("");

        var httpURI = null;
        var xmppJID = null;
        if (lj("#mobidickCallBackMethod").prop("checked")) {
            httpURI = "mobidick";
        } else if (lj("#httpCallBackMethod").prop("checked")) {
            httpURI = lj("#httpCallBackURI").val();
            if (httpURI != "mobidick") {
                var httpPattern = /^(http|https):\/\/[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?$/g;
                if (!httpURI.match(httpPattern)) {
                    lj("#validationError").text(
                            "The http address is not valid.");
                    lj("#httpCallBackMethod").focus();
                    return;
                }
            }
        } else {
            lj("#validationError").text(
                    "Select the way the callbacks are delivered. HTTP(s)/XMPP");
            return;
        }

        mctracker.call({
            url : '/mobi/rest/service/update_callback_configuration',
            type : 'POST',
            data : {
                data : JSON.stringify({
                    httpURI : httpURI,
                    xmppJID : xmppJID
                })
            },
            success : function(data, textStatus, XMLHttpRequest) {
                configuration2Screen(data);
            },
            error : function(data, textStatus, XMLHttpRequest) {
                mctracker.showAjaxError(XMLHttpRequest, textStatus, data);
            }
        });
    };

    var addAPIKeyToUI = function (ak) {
        ak.date = mctracker.formatDate(ak.timestamp);
        var gatml = $.tmpl(ak_template, ak);
        gatml.hide();
        lj("#apiKeys").append(gatml);
        gatml.fadeIn('slow');
        $("a", gatml).click(function () {
            lj("#apiKeyNameLabel", "dc").text(ak.name);
            apiKeyToDeleteDetails = ak;
            lj("#deleteAPIKey", "d").dialog('open');
        });
    };

    var addCallbackConfigToUI = function(cc) {
        cc.date = mctracker.formatDate(cc.created);
        var gatml = $.tmpl(cc_template, cc);
        gatml.hide();
        lj("#callbackConfigs").append(gatml);
        gatml.fadeIn('slow');
        $("a.cc-test", gatml).click(function () {
            var textarea = lj("#logWindow", "dc");
            textarea.val("Launching testcallback...\n");
            lj("#interactiveLoggingDialog", "d").dialog('open');

            mctracker.call({
                url: '/mobi/rest/service/test_callback_configuration',
                type: 'POST',
                data: {
                    data: JSON.stringify({
                        name: cc.name
                    })
                },
                success: function  (data, textStatus, XMLHttpRequest) {
                    textarea.val(textarea.val()+"Succesfully launched test callback, result will be posted.\n");
                },
                error: function (data, textStatus, XMLHttpRequest) {
                    mctracker.showAjaxError(XMLHttpRequest, textStatus, data);
                }
            });
        });
        $("a.cc-edit", gatml).click(function () {
            console.log('edit cicked');
            lj("#addCallbackConfigDialog", "d").dialog('open');
            lj("#addCallbackConfigDialog_name", "dc").val(cc.name);
            lj("#addCallbackConfigDialog_httpCallBackURI", "dc").val(cc.uri);

            if (cc.regexes.length > 0) {
                lj("#addCallbackConfigDialog_regex", "dc").val(cc.regexes[0]);

                lj("#addCallbackConfigDialog_sectionRegex", "dc").show();
                lj("#addCallbackConfigDialog_sectionCallback", "dc").hide();
            } else {

            	lj("#addCallbackConfigDialog_sectionRegex", "dc").hide();
                lj("#addCallbackConfigDialog_sectionCallback", "dc").show();

                lj("#addCallbackConfigDialog_sectionCallback input[type=checkbox]", "dc").each(function () {
                	if (cc.callbacks == -1) {
                		$(this).attr('checked', false);
                	} else {
                		var code = $(this).attr('code');
                        if (code) {
                            code = new Number(code);
                            $(this).attr('checked', ((cc.callbacks & code) == code));
                        }
                	}
                });
            }
            lj("#addCallbackConfigDialog_customHeaders", "dc").val(cc.custom_headers);

        });
        $("a.cc-delete", gatml).click(function () {
            lj("#callbackConfigNameLabel", "dc").text(cc.name);
            callbackConfigNameToDeleteDetails = cc;
            lj("#deleteCallbackConfigDialog", "d").dialog('open');
        });
    };

    var configuration2Screen = function (configuration) {
        lj("#validationError").empty();
        lj("#apiKeys").empty();
        var elements = lj("*").removeAttr('disabled')
            .not(lj("#chkEnabled"))
            .not(lj("#testConfiguration"))
            .not(lj("#saveConfiguration"));
        if (! configuration.apiKeys || configuration.apiKeys.length == 0) {
            elements.fadeTo('slow', 1);
        } else {
            elements.not(lj("#noAPIKeys").hide()).fadeTo('slow', 1);
            $.each(configuration.apiKeys, function(index, val) {addAPIKeyToUI(val);});
        }
        lj("#apiActionPoints").empty().append($.tmpl(ai_template, configuration));
        var canBeEnabled = configuration.actions.length == 0;
        if (canBeEnabled)
            lj("#actionPoints, #apiActionPoints").hide();
        lj("#actionPoints").css('display', canBeEnabled ? 'none':'block');
        lj("#chkEnabled").prop('checked', configuration.enabled).attr('disabled', ! canBeEnabled).fadeTo('slow', canBeEnabled ? 1:0.6);
        lj("#chkEnabledLabel").fadeTo('slow', canBeEnabled ? 1:0.6);
        lj("#testConfiguration").attr('disabled', ! configuration.needsTestCall).fadeTo('slow', configuration.needsTestCall ? 1:0.6);
        if ( configuration.needsTestCall )
            lj("#testConfiguration").removeAttr('disabled');
        lj("#saveConfiguration").attr('disabled', true).fadeTo('slow', 0.6);
        lj("#httpCallBackSecret").text(configuration.sik);
        lj("#callBackFromJid").text(configuration.callBackFromJid);
        if (configuration.callBackURI) {
            if (configuration.callBackURI == "mobidick") {
                lj("#mobidickCallBackMethod").prop("checked", true);
                lj("#httpCallBackURI").val("");
            } else {
                lj("#httpCallBackMethod").prop("checked", true);
                lj("#httpCallBackURI").val(configuration.callBackURI);
            }
        }
        lj("#callbackRpcDetailsContainer input[type=checkbox]").each(function () {
            var code = $(this).attr('code');
            if (code) {
                code = new Number(code);
                $(this).attr('checked', ((configuration.callbacks & code) == code)).change(function () {
                    mctracker.call({
                        url: '/mobi/rest/service/enable_callback',
                        type: 'post',
                        data: {
                            data: JSON.stringify({
                                callback: code,
                                enabled: $(this).prop('checked')
                            })
                        }
                    });
                });
            }
        });
        if (configuration.enabled) {
            if (configuration.mobidickUrl) {
                lj("#mobidick").show();
                lj("#mobidick_link")
                    .text("Open Mobidick sample service control panel")
                    .attr("href", configuration.mobidickUrl)
                    .attr("target", "_blanc");
            } else {
                lj("#mobidick").hide();
            }
            $("#callbackConfigContainer").show();
            lj("#createRegexCallbackConfig").button().click(function () {
                lj("#addCallbackConfigDialog", "d").dialog('open');
                lj("#addCallbackConfigDialog_sectionRegex", "dc").show();
                lj("#addCallbackConfigDialog_sectionCallback", "dc").hide();
            });
            lj("#createCallbackConfig").button().click(function () {
                lj("#addCallbackConfigDialog", "d").dialog('open');
                lj("#addCallbackConfigDialog_sectionRegex", "dc").hide();
                lj("#addCallbackConfigDialog_sectionCallback", "dc").show();
            });
            lj("#callbackConfigs").empty();
            if (configuration.regexCallbackConfigurations.length > 0) {
                $.each(configuration.regexCallbackConfigurations, function(index, val) {addCallbackConfigToUI(val);});
            }

        } else {
            if (!configuration.callBackURI) {
                lj("#mobidick").show();
                lj("#mobidick_link")
                    .text("Use Mobidick sample service")
                    .click(configure_mobidick);
            } else {
                lj("#mobidick").hide();
            }
            $("#callbackConfigContainer").hide();
        }
        if (configuration.updatesPending) {
            $("#svcUpdatesPending").fadeIn('slow');
        } else {
            $("#svcUpdatesPending").fadeOut('fast');
        }
    };

    var configure_mobidick = function () {
        mctracker.call({
            url: '/mobi/rest/service/configure_mobidick',
            type: 'POST',
            data: {
                data: JSON.stringify({})
            },
            success: function  (data, textStatus, XMLHttpRequest) {
                window.location = "/";
            },
            error: function (data, textStatus, XMLHttpRequest) {
                mctracker.showAjaxError(XMLHttpRequest, textStatus, data);
            }
        });

    };

    var loadScreen = function () {
        mctracker.call({
            url: '/mobi/rest/service/get_configuration',
            type: 'GET',
            success: function  (data, textStatus, XMLHttpRequest) {
                if (data) {
                    configuration2Screen(data);
                } else {
                    lj("#user", "dc").text(loggedOnUserEmail);
                    lj("#convertAccountToServiceDialog", "d").dialog('open');
                }
            },
            error: function (data, textStatus, XMLHttpRequest) {
                mctracker.showAjaxError(XMLHttpRequest, textStatus, data);
            }
        });
        loadAdmins();
    };

    var loadAdmins = function () {
        mctracker.call({
            url: '/mobi/rest/service/grants',
            type: 'GET',
            success: function  (data, textStatus, XMLHttpRequest) {
                var admins = [];
                $.each(data, function (i, grant){
                   if (grant.role_type == "admin") {
                       admins.push(grant);
                   }
                });
                var templ = "{{each admins}}<li>${$value.user_name} &lt;${$value.user_email}&gt; (${$value.role}) <a class=\"action-link\" admin_email=\"${$value.user_email}\" admin_role=\"${$value.role}\" service_identity=\"${$value.identity}\">revoke</a></li>{{/each}}";
                $("a", lj("#serviceAdministrators").empty().append($.tmpl(templ, {admins:admins}))).click(function () {
                    var admin_email = $(this).attr("admin_email");
                    var admin_role = $(this).attr("admin_role");
                    var service_identity = $(this).attr("service_identity");
                    mctracker.call({
                        url: '/mobi/rest/service/admin/roles/revoke',
                        type: 'POST',
                        data: {
                            data: JSON.stringify({
                                user_email: admin_email,
                                role: admin_role,
                                identity: service_identity
                            })
                        },
                        success: function  (data, textStatus, XMLHttpRequest) {
                        }
                    });
                });
            }
        });
    };

    var publishPendingChanges = function() {
        mctracker.confirm("Are you sure you wish to publish the changes?", function() {
            mctracker.call({
                url : '/mobi/rest/service/publish_changes',
                type : 'POST',
                data : {
                    data : JSON.stringify({})
                },
                success : function(data, textStatus, XMLHttpRequest) {
                    $("#svcUpdatesPending").fadeOut('fast');
                },
                error : mctracker.showAjaxError
            });
        });
    };

    var processMessage = function (data) {
        if (data.type == 'rogerthat.service.testCallSucceeded') {
            lj("#testConfiguration").attr('disabled', true).fadeTo('slow', 0.6);
            alert('Test callback round trip succeeded !');
            if (data.callback_name == null) {
                window.location = "/";
            }
        } else if (data.type == 'rogerthat.service.interactive_logs') {
            var textarea = lj("#logWindow", "dc");
            textarea.val(textarea.val()+"Status: "+ data.status +"\nContent-type: "+ data.content_type +"\nResult url: "+ data.result_url +"\n\n"+ data.body);
        } else if (data.type == 'rogerthat.service.adminsChanged') {
            loadAdmins();
        } else if (data.type == 'rogerthat.service.updatesPendingChanged') {
            if (data.updatesPending) {
                $("#svcUpdatesPending").fadeIn('slow');
            } else {
                $("#svcUpdatesPending").fadeOut('fast');
            }
        }
    };

    return function () {
        mctracker.registerMsgCallback(processMessage);
        mctracker.setOnLoadContainer(function (container) {
            if (container == container_name)
                loadScreen();
        });

        applyJQueryInUI();
    };
};

mctracker.registerLoadCallback("servicePanelContainer", serviceScript());
