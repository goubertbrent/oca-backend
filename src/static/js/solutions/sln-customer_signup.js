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

    var customerSignupMessages = {};
    var customerSignupMessageRequests = {};
    var isWaitingForProvisionUpdate = false;

    var allowedBroadcastTypes = [];
    var allowedModules = {};

    var loadCustomerSignups = function() {
        sln.call({
            url: '/common/customer/signup/all',
            type: 'get',
            success: function(data) {
                $.each(data, function(i, signup) {
                    var chatId = signup.inbox_message_key;
                    if(chatId) {
                        customerSignupMessages[chatId] = signup;
                        if(customerSignupMessageRequests[chatId]) {
                            addSignupActionsToMessage(chatId, signup);
                            delete customerSignupMessageRequests[chatId];
                        }
                    }
                });
            },
            error: sln.showAjaxError
        });
    };

    var signupAction = function(signupKey, ok) {
        event.stopPropagation();

        if(ok) {
            signupCustomer(signupKey);
        } else {
            sendReply(signupKey);
        }
    };

    var getAllowedModulesAndBroadcastTypes = function(signupKey, callback) {
        if(allowedModules[signupKey] && allowedBroadcastTypes.length) {
            callback(allowedModules[signupKey], allowedBroadcastTypes);
        } else {
            sln.call({
                url: '/common/customer/signup/get_defaults',
                type: 'get',
                data: {
                    signup_key: signupKey
                },
                success: function(data){
                    allowedModules[signupKey] = data.modules;
                    allowedBroadcastTypes = data.broadcast_types;
                    callback(data.modules, data.broadcast_types);
                },
                error: sln.showAjaxError
            });
        }
    };

    var signupCustomer = function(signupKey) {
        sln.confirm(CommonTranslations.create_service_for_signup_request, createService);

        function createService() {
            // get allowed/default modules and broadcast types
            getAllowedModulesAndBroadcastTypes(signupKey, doCreateService);

            function doCreateService(modules, broadcastTypes) {
                var defaultModules = [];
                $.each(modules, function(i, module) {
                    if(module.is_default) {
                        defaultModules.push(module.key);
                    }
                });

                sln.showProcessing(CommonTranslations.LOADING_DOT_DOT_DOT);
                isWaitingForProvisionUpdate = true;

                sln.call({
                    url: '/common/signup/services/create',
                    type: 'post',
                    data: {
                        signup_key: signupKey,
                        modules: defaultModules,
                        broadcast_types: broadcastTypes
                    },
                    success: function(data) {
                        if(!data.success) {
                            isWaitingForProvisionUpdate = false;
                            sln.hideProcessing();
                            sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                        }
                        // will be updated through the channel
                    },
                    error: sln.showAjaxError
                });
            }
        }
    };

    var sendReply = function(signupKey) {
        sln.inputBox(function(message) {
            sln.call({
                url: '/common/customer/singup/reply',
                type: 'post',
                data: {
                    signup_key: signupKey,
                    message: message
                },
                success: function(data) {
                    if(!data.success) {
                        sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    }
                },
                error: sln.showAjaxError
            });
        },
        CommonTranslations.reason, CommonTranslations.SEND, CommonTranslations.signup_not_ok, null, null, '', true);
    };

    var getSignupButtonGroup = function(signup, onRight) {
        var group = $('<div class="btn-group"></div>').attr('signup_key', signup.key);

        var btnOk = $('<button action="ok" class="btn btn-large btn-success"><i class="fa fa-check"></i> ' + CommonTranslations['reservation-approve'] + '</button>').attr('key', signup.key);
        var btnNotOk = $('<button action="notok" class="btn btn-large btn-warning"><i class="fa fa-times"></i> ' + CommonTranslations['reservation-decline'] + '</button>').attr('key', signup.key);

        btnOk.click(function() {
            signupAction(signup.key, true);
        });
        btnNotOk.click(function() {
            signupAction(signup.key, false);
        });

        group.append(btnOk);
        group.append(btnNotOk);
        if(onRight) {
            group.addClass("pull-right");
        }
        return group;
    };

    var getActionsForCustomerSignup = function (signup) {
        var toolbar = $('<div class="btn-toolbar"></div>').attr('signup_key', signup.key);
        var group = getSignupButtonGroup(signup);
        toolbar.append(group);
        return toolbar;
    };

    var addSignupActionsToMessage = function(chatId, signup) {
        sln.setInboxActions(chatId, getActionsForCustomerSignup(signup));
    };

    var channelUpdates = function (data) {
        switch (data.type) {
            case 'solutions.common.customer.signup.update':
                loadCustomerSignups();
                break;
            case 'common.provision.success':
                if(isWaitingForProvisionUpdate) {
                    isWaitingForProvisionUpdate = false;
                    sln.hideProcessing();
                    sln.alert(CommonTranslations.service_created, null, CommonTranslations.SUCCESS);
                }
                break;
            case 'common.provision.failed':
                if(isWaitingForProvisionUpdate) {
                    isWaitingForProvisionUpdate = false;
                    sln.hideProcessing();
                    sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                }
                break;
        }
    };


    sln.registerMsgCallback(channelUpdates);
    loadCustomerSignups();

    sln.registerInboxActionListener("customer_signup", function (chatId) {
        var signup = customerSignupMessages[chatId];
        if(signup) {
            addSignupActionsToMessage(chatId, signup);
        } else {
            customerSignupMessageRequests[chatId] = chatId;
        }
    });

    // add signup toolbar buttons when opening the message
    var inboxReply = $('#inbox-reply');
    $(document).on("click", '.inbox-message-action-reply', function(event) {
        var chatId = $(this).attr('message_key');
        var signup = customerSignupMessages[chatId];
        // remove the previous signup button group if any
        var prevButtonGroup = inboxReply.find('.btn-toolbar .btn-group').last();
        if(prevButtonGroup.attr('signup_key')) {
            prevButtonGroup.remove();
        }
        // add the button group if it's a signup message
        if(signup) {
            var buttonGroup = getSignupButtonGroup(signup, true);
            inboxReply.find('.btn-toolbar .btn-group').last().after(buttonGroup);
        }
    });

});
