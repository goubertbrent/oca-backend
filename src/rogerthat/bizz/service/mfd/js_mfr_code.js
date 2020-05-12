/*
 * Copyright 2019 Green Valley Belgium NV
 * NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
 * Copyright 2018 GIG Technology NV
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
 * @@license_version:1.6@@
 */

var flowDefinition;
var WIDGET_RESULT_MAP; // this var is generated in mfr_template, as well as all form types
var returnScriptable = undefined; // this var is overwritten by android devices
var adjustedTimeDiff = 0;

/* Step types */
var STEP_TYPE_END = 'end';
var STEP_TYPE_FLUSH = 'flush';
var STEP_TYPE_EMAIL = 'email';
var STEP_TYPE_MESSAGE = 'message';
var STEP_TYPE_FLOW_CODE = 'flow_code';

/* Message type */
var MESSAGE_TYPE_MESSAGE = 'message_step';
var MESSAGE_TYPE_FORM = 'form_step';

var FORM_POSITIVE = 'positive';
var FORM_NEGATIVE = 'negative';

var ROGERTHAT_BUTTON_CAPTION = 'Roger that';

/* Api functions */
var API_PRESS_MENU_ICON = 'com.mobicage.api.services.pressMenuItem';
var API_START_SVC_ACTION = 'com.mobicage.api.services.startAction';

var API_NEW_FLOW_MESSAGE = 'com.mobicage.api.messaging.jsmfr.newFlowMessage';
var API_FLOW_MEMBER_RESULT = 'com.mobicage.api.messaging.jsmfr.messageFlowMemberResult';
var API_FLOW_FINISHED = 'com.mobicage.api.messaging.jsmfr.messageFlowFinished';
var CAPI_FLOW_FINISHED = 'com.mobicage.capi.messaging.endMessageFlow';

// When a flow is started locally by com.mobicage.capi.messaging.startFlow
var API_FLOW_STARTED = 'com.mobicage.api.messaging.jsmfr.flowStarted';

var API_UPDATE_USER_DATA = 'com.mobicage.api.services.updateUserData';
var CAPI_UPDATE_USER_DATA = 'com.mobicage.capi.services.updateUserData';

function createIncomingJsonCall(funcName, request) {
    var r = {};
    r['av'] = 1;
    r['t'] = now();
    r['ci'] = '_js_callid_' + GUID();
    r['f'] = funcName;
    r['a'] = {
        "request": request
    };
    return r;
}

function getUIFlagsByButtonReferenceId(refId) {
    var btnRef = flowDefinition[refId];

    while (btnRef.step_type == STEP_TYPE_FLUSH || btnRef.step_type == STEP_TYPE_EMAIL)
        btnRef = flowDefinition[btnRef.reference];

    if (btnRef.step_type == STEP_TYPE_END)
        return btnRef.wff ? 1 : 0;

    return 1;
}

function getFormDisplayValue(message, formResult) {
    if (!formResult || !formResult.result)
        return null;

    var result = formResult.result;

    if ([FORM_TEXT_LINE, FORM_TEXT_BLOCK, FORM_AUTO_COMPLETE, FORM_PHOTO_UPLOAD].indexOf(message.form.type) != -1) {
        return result.value;
    }
    if (message.form.type == FORM_SINGLE_SELECT) {
        for (var i = 0; i < message.form.widget.choices.length; i++) {
            var choice = message.form.widget.choices[i];
            if (choice.value === result.value)
                return choice.label;
        }
    }
    if (message.form.type == FORM_MULTI_SELECT) {
        var choices = [];
        for (var i = 0; i < message.form.widget.choices.length; i++) {
            var choice = message.form.widget.choices[i];
            if (result.values.indexOf(choice.value) !== -1)
                choices.push(choice.label);
        }
        return choices.join("\n");
    }

    if (message.form.type == FORM_DATE_SELECT) {
        var timeZoneOffset = 60 * new Date().getTimezoneOffset();
        var d = new Date((timeZoneOffset + result.value) * 1000);

        var timeString = function() {
            var hours = d.getHours();
            var minutes = d.getMinutes();
            if (minutes < 10)
                minutes = "0" + minutes;
            return hours + ":" + minutes;
        };
        var dateString = function() {
            var monthNames = [ "January", "February", "March", "April", "May", "June", "July", "August", "September",
                    "October", "November", "December" ];
            return monthNames[d.getMonth()] + ' ' + d.getDate() + ' ' + d.getFullYear();
        };
        var resultString = function() {
            if ("date" == message.form.widget.mode)
                return dateString();
            if ("time" == message.form.widget.mode)
                return timeString();
            return dateString() + " " + timeString();
        };
        return (message.form.widget.unit || "<value/>").replace("<value/>", resultString());
    }

    if (message.form.type == FORM_SINGLE_SLIDER) {
        return (message.form.widget.unit || "<value/>").replace("<value/>", result.value);
    }

    if (message.form.type == FORM_RANGE_SLIDER) {
        var p = message.form.widget.precision;
        return (message.form.widget.unit || "<low_value/> - <high_value/>").replace("<low_value/>",
            result.values[0].toFixed(p)).replace("<high_value/>", result.values[1].toFixed(p));
    }

    if (message.form.type == FORM_GPS_LOCATION) {
        return "(" + result.latitude.toFixed(3) + ", " + result.longitude.toFixed(3) + ") +/- "
            + result.horizontal_accuracy.toFixed(2) + "m\nhttps://www.google.com/maps/preview?daddr="
            + result.latitude + "," + result.longitude;
    }

    if (message.form.type == FORM_MYDIGIPASS) {
        var lines = [];
        if (result.eid_profile !== null) {
            var eidProfileParts = [];
            var nameParts = [result.eid_profile.first_name, result.eid_profile.last_name];
            if (result.eid_profile.first_name3) {
                nameParts.insert(result.eid_profile.first_name3, 1);
            }
            eidProfileParts.push("* Name: " + nameParts.join(" "));
            eidProfileParts.push("* Gender: " + result.eid_profile.gender);
            eidProfileParts.push("* Nationality: " + result.eid_profile.nationality);
            eidProfileParts.push("* Date of birth: " + result.eid_profile.date_of_birth + ", "
                + result.eid_profile.location_of_birth);
            eidProfileParts.push("* Noble condition: " + result.eid_profile.noble_condition || "");
            eidProfileParts.push("* Issuing municipality: " + result.eid_profile.issuing_municipality);
            eidProfileParts.push("* Validity: from "
                + (new Date(result.eid_profile.validity_begins_at)).toLocaleDateString() + " to "
                + (new Date(result.eid_profile.validity_ends_at)).toLocaleDateString());
            eidProfileParts.push("* Created at: " + (result.eid_profile.created_at || ""));
            eidProfileParts.push("* Card number: " + result.eid_profile.card_number);
            eidProfileParts.push("* Chip number: " + result.eid_profile.chip_number);
            lines.push("eID profile:\n" + eidProfileParts.join("\n"));
        }
        if (result.eid_address !== null) {
            lines.push("eID address: " + result.eid_address.street_and_number + ", " + result.eid_address.zip_code
                + " " + result.eid_address.municipality);
        }
        if (result.eid_photo !== null) {
            lines.push("eID photo: see attachment");
        }
        if (result.email !== null) {
            lines.push("E-mail: " + result.email);
        }
        if (result.phone !== null) {
            lines.push("Phone: " + result.phone);
        }
        if (result.profile !== null) {
            var profileParts = [];
            profileParts.push("* Name: " + (result.profile.first_name || "") + " " + (result.profile.last_name || ""));
            profileParts.push("* Language: " + result.profile.preferred_locale);
            profileParts.push("* Born on: " + result.profile.born_on);
            profileParts.push("* UUID: " + result.profile.uuid);
            var dateStr;
            if (result.updated_at) {
                var d = new Date(result.profile.updated_at);
                dateStr = d.toLocaleDateString() + " " + timeString(d);
            } else {
                dateStr = "";
            }
            profileParts.push("* Updated at: " + dateStr);
            lines.push("Profile:\n" + profileParts.join("\n"));
        }
        if (result.address !== null) {
            var addressParts = [];
            if (result.address.address_1)
                addressParts.push(result.address.address_1);
            if (result.address.address_2)
                addressParts.push(result.address.address_2);
            var cityParts = [];
            if (result.address.zip)
                cityParts.push(result.address.zip);
            if (result.address.city)
                cityParts.push(result.address.city);
            if (cityParts.length)
                cityParts.push(cityParts.join(" "));
            if (result.address.state)
                addressParts.push(result.address.state);
            if (result.address.country)
                addressParts.push(result.address.country);
            lines.push("Address: " + addressParts.join(", "));
        }
        return lines.join("\n\n");
    }

    if (message.form.type === FORM_ADVANCED_ORDER) {
        var lines = [];
        for (var i = 0, categoryCount = result.categories.length; i < categoryCount; i++) {
            var category = result.categories[i];
            if (i !== 0) {
                lines.push('');
            }
            lines.push(category.name + ':');
            for (var j = 0, itemCount = category.items.length; j < itemCount; j++) {
                var item = category.items[j];
                var unit = item.step_unit ? item.step_unit : item.unit;
                lines.push('\t* ' + item.name + ', ' + item.value + ' ' + unit);
            }
        }
        return lines.join("\n");
    }

    if (message.form.type == FORM_FRIEND_SELECT) {
        return result.values.join("\n");
    }

    if (message.form.type == FORM_SIGN) {
        return "Signed";
    }

    if (message.form.type == FORM_OAUTH) {
        return "Successfully authorized";
    }

    if (message.form.type == FORM_PAY) {
        var lines = [];
        lines.push("Via: " + result.provider_id);
        lines.push("Ref.: " + result.transaction_id);
        lines.push("Status: " + result.status);
        return lines.join("\n");
    }

    if (message.form.type === FORM_OPENID) {
        var lines = [];
        if (result.given_name != null) {
            lines.push('First name: ' + result.given_name);
        }
        if (result.family_name != null) {
            lines.push('Family name: ' + result.family_name);
        }
        if (result.gender != null) {
            lines.push('Gender: ' + result.gender);
        }
        if (result.birthdate != null) {
            lines.push('Birth date: ' + result.birthdate);
        }
        if (result.locale != null) {
            lines.push('Language: ' + result.locale);
        }
        if (result.email != null) {
            lines.push('Email: ' + result.email);
        }
        if (result.phone_number != null) {
            lines.push('Phone number: ' + result.phone_number);
        }
        if (result.address !== null) {
            if (result.address.street_address != null) {
                lines.push('Address: ' + result.address.street_address.replace('\n', ', '));
            }
            if (result.address.postal_code != null) {
                lines.push('Postal code: ' + result.address.postal_code);
            }
            if (result.address.locality != null) {
                lines.push('Locality: ' + result.address.locality);
            }
            if (result.country != null) {
                lines.push('Country: ' + result.address.country);
            }
        }
        return lines.join('\n');
    }

    return "";
}

function processEndStep(state, endDef, localActions, serverActions) {
    var request = {
        message_flow_run_id: state.run.message_flow_run_id,
        parent_message_key: state.run.parent_message_key,
        end_id: endDef.id,
        wait_for_followup: endDef.wff
    };
    localActions.push(createIncomingJsonCall(CAPI_FLOW_FINISHED, request));
    serverActions.push(createIncomingJsonCall(API_FLOW_FINISHED, request));
}

function processResultsFlush(state, flushDef) {
    var request = {
        flush_id: flushDef.id,
        end_id: flowDefinition[flushDef.reference].step_type == STEP_TYPE_END ? flushDef.reference : null,
        run: cloneObj(state.run),
        timestamp: now()
    };

    return createIncomingJsonCall(API_FLOW_MEMBER_RESULT, request);
}

function processResultsEmail(state, flushDef) {
    var request = {
        flush_id: flushDef.id,
        end_id: flowDefinition[flushDef.reference].step_type == STEP_TYPE_END ? flushDef.reference : null,
        run: cloneObj(state.run),
        email_admins: flushDef.email_admins,
        emails: flushDef.emails,
        results_email: true,
        message_flow_name: flowDefinition.name
    };

    return createIncomingJsonCall(API_FLOW_MEMBER_RESULT, request);
}

function getFlowcodeLocals(state) {
    var flowParams = {};
    try {
        flowParams = JSON.parse(state.run.flow_params);
    } catch (e) {
        // Couldn't parse flow params
    }
    return {
        rogerthat: {
            user: cloneObj(state.user),
            service: cloneObj(state.service),
            system: cloneObj(state.system)
        },
        messageFlowRun: {
            steps: cloneObj(state.run.steps),
            flow_id: cloneObj(state.run.message_flow_run_id),
            flow_params: flowParams || {}
        },
        window: {},
        document: {}
    };
}

function processFlowCode(state, flowDef, localActions, serverActions) {
    var locals = getFlowcodeLocals(state);

    locals.rogerthat.user.put = function() {
        var req = {
            service : state.run.sender,
            user_data : JSON.stringify(locals.rogerthat.user.data)
        };
        localActions.push(createIncomingJsonCall(CAPI_UPDATE_USER_DATA, req));
        serverActions.push(createIncomingJsonCall(API_UPDATE_USER_DATA, req));
    };

    // create our own this object for the user code
    var that = Object.create(null);
    // add translations to flow code
    var js_code = addTranslationToCode(flowDef.javascript_code);
    var code = js_code
        + ' try{ return {nsr: run(rogerthat, messageFlowRun), error: null }; } catch(ex){ return {nsr: null, error: ex };}';
    try {
        var s = createSandbox(code, that, locals)(); // call the user code in the sandbox
        if (s.nsr === undefined || s.nsr === null || s.error === undefined || s.error !== null) {
            if (s.error) {
                addLogToServer(serverActions, s.error, code);
            }
            return flowDef.exception_reference;
        }

        if (s.nsr.outlet === undefined || s.nsr.outlet === null) {
            addLogToServer(serverActions, {
                "name": "NextStepResult outlet was null",
                "message": "NextStepResult may not be null, following exception path."
            }, code);
            return flowDef.exception_reference;
        }

        if (s.nsr.outlet in flowDef.outlets) {
            var nextOutlet = flowDef.outlets[s.nsr.outlet];
            var nextStepDef = flowDefinition[nextOutlet];

            while (nextStepDef.step_type == STEP_TYPE_FLUSH || nextStepDef.step_type == STEP_TYPE_EMAIL) {
                nextStepDef = flowDefinition[nextStepDef.reference];
            }
            state.run.flowCode = {
                stepCount: state.run.steps.length,
                defaultValue: null,
                form: null,
                message: s.nsr.message || null,
                answers: null,
                attachments: null,
            };
            if (nextStepDef.message_type == MESSAGE_TYPE_MESSAGE) {
                if (s.nsr.answers) {
                    state.run.flowCode.answers = s.nsr.answers;
                }
            } else if (nextStepDef.message_type == MESSAGE_TYPE_FORM) {
                if (s.nsr.defaultValue) {
                    state.run.flowCode.defaultValue = s.nsr.defaultValue;
                }
                if (s.nsr.form) {
                    state.run.flowCode.form = s.nsr.form;
                }
            }
            state.run.flowCode.attachments = s.nsr.attachments;
            return nextOutlet;
        } else {
            return flowDef.exception_reference;
        }
    } catch (ex) {
        addLogToServer(serverActions, ex, code);
        return flowDef.exception_reference;
    }

    function addLogToServer(serverActions, ex, code) {
        var message = "Type: " + ex.name;
        message += "\nMessage: " + ex.message;
        message += "\nCode:\n" + code;

        request = {
            mobicageVersion : "",
            platform : 4,
            platformVersion : "",
            errorMessage : message,
            description : "",
            timestamp: now()
        };
        serverActions.push(createIncomingJsonCall('com.mobicage.api.system.logError', request));
    }

    function createSandbox(code, that, locals) {
        var params = []; // the names of local variables
        var args = []; // the local variables

        for (var param in locals) {
            if (locals.hasOwnProperty(param)) {
                args.push(locals[param]);
                params.push(param);
            }
        }

        // create the parameter list for the sandbox
        var context = Array.prototype.concat.call(that, params, code);
        // create the sandbox function
        var sandbox = new (Function.prototype.bind.apply(Function, context));
        // create the argument list for the sandbox
        context = Array.prototype.concat.call(that, args);
        // bind the local variables to the sandbox
        return Function.prototype.bind.apply(sandbox, context);
    }
}

function mergeObjects(fromObj, toObj) {
    for (var i in fromObj) {
        if (fromObj.hasOwnProperty(i)) {
            if (!toObj.hasOwnProperty(i)) {
                throw new Error('Trying to set unknown property "' + i + '" on ' + JSON.stringify(toObj));
            }
            toObj[i] = fromObj[i];
        }
    }
}

function setAnswers(state, action) {
    var answers = state.run.flowCode.answers;
    if (!answers)
        return;

    var buttons = action.request.message.buttons;
    for (var i = 0; i < buttons.length; i++) {
        var btn = buttons[i];
        var answer = answers[btn.id.replace(/^button_/, "")];
        if (answer) {
            answer.id = btn.id;
            if (answer.action && answer.action.indexOf('smi://') == 0) {
                answer.action = 'smi://' + sha256(answer.action.substring(6));
            }
            mergeObjects(answer, btn);
        }
    }
}

/* from rogerthat-1.0.js */
function rogerthatTranslate(key, parameters) {
    // this should be added an existing rogerthat context
    // e.g. rogerthat.translate = rogerthatTranslate.bind(rogerthat);
    var language = this.user.language || this.util._translations.defaultLanguage;
    var translation = undefined;
    if (language != this.util._translations.defaultLanguage) {
        var translationSet = this.util._translations.values[key];
        if (translationSet) {
            translation = translationSet[language];
            if (translation === undefined) {
                if (language.indexOf('_') != -1) {
                    language = language.split('_')[0];
                    translation = translationSet[language];
                }
            }
        }
    }

    if (translation == undefined) {
        // language is defaultLanguage / key is missing / key is not translated
        translation = key;
    }

    if (parameters) {
        $.each(parameters, function(param, value) {
            translation = translation.replace('%(' + param + ')s', value);
        });
    }
    return translation;
}

function getAlternativeRunFunc() {
    return function run() {
        var rogerthat = arguments[rogerthatArgPosition];

        if (rogerthat) {
            if (!rogerthat.util) {
                rogerthat.util = {};
            }
            rogerthat.util._translations = rogerthat_translations;
            rogerthat.util.translate = rogerthatTranslate.bind(rogerthat);
        }

        return _run.apply(null, arguments);
    }
}

var runFuncRegex = /(function|var)\s+run\s*(=\s*function|\()/;
/*  Adds the translations to validation or flow code block (string)
    by combining the translation values with rogerthatTranslate() and
    an alternative run function in the form of e.g.

    var rogerthat_translations = {
        "values": {
            "key1": null
        },
        "defaultLanguage":"en"
    };

    // alternative run function
    var run = function(result, rogerthat) {
        if (rogerthat) {
            rogerthat.util._translations = rogerthat_translations;
            rogerthat.util.translate = rogerthatTranslate;
        }
        return _run(result, rogerthat);
    };

    // original run func
    var _run = function(result, rogerthat) {
        return result.value ? true : rogerthat.utils.translate('This field is required');
    };
*/
function addTranslationToCode(codeBlock, isValidation) {
    if (!runFuncRegex.test(codeBlock)) {
        throw new Error('codeBlock must contain a run function');
    }

    if (typeof isValidation !== 'boolean') {
        isValidation = false;
    }

    // replace run with _run in the matched definition
    // form of the run function (var function)
    var match = codeBlock.match(runFuncRegex)[0];
    var replacement = match.replace('run', '_run');

    return [
        'var rogerthat_translations = ' + JSON.stringify(flowDefinition.translations) + ';',
        rogerthatTranslate.toString(),
        getAlternativeRunFunc().toString().replace('rogerthatArgPosition', +isValidation),
        codeBlock.replace(match, replacement)
    ].join('\n\n');
}

function setFormSettings(state, action) {
    var fcF = state.run.flowCode.form;
    if (!fcF)
        return;

    var acF = action.request.form_message.form;
    if (fcF.type && fcF.type != acF.type) {
        throw new Error('Exception form type "' + acF.type + '", but got "' + fcF.type + '"');
    }

    var formSettings = ['positive_button', 'positive_confirmation', 'positive_button_ui_flags', 'negative_button',
        'negative_confirmation', 'negative_button_ui_flags', 'javascript_validation'];
    for (var i in formSettings) {
        var setting = formSettings[i];
        if (fcF[setting] !== undefined && fcF[setting] !== null)
            acF[setting] = fcF[setting];
    }

    var fcW = fcF.widget;
    if (fcW) {
        var acW = acF.widget;
        mergeObjects(fcW, acW);
        if (acF.type == FORM_AUTO_COMPLETE) {
            if (fcW.suggestions && !fcW.choices) {
                acW.choices = fcW.suggestions;
            }
        } else if (acF.type == FORM_DATE_SELECT) {
            if (fcW.date !== undefined)
                acW.has_date = true;
            if (fcW.min_date !== undefined)
                acW.has_min_date = true;
            if (fcW.max_date !== undefined)
                acW.has_max_date = true;
        }
    }
}

function setDefaultValue(state, action) {
    var v = state.run.flowCode.defaultValue;
    if (!v)
        return;

    var f = action.request.form_message.form;
    var w = f.widget;
    if ([FORM_TEXT_LINE, FORM_TEXT_BLOCK, FORM_AUTO_COMPLETE].indexOf(f.type) >= 0) {
        if (typeof (v) == "string") {
            w.value = v;
        }
    } else if (f.type === FORM_SINGLE_SELECT) {
        if (typeof (v) === "string") {
            for (var i = 0; i < w.choices.length; i++) {
                if (w.choices[i].value === v) {
                    w.value = v;
                    break;
                }
            }
        }
    } else if (f.type === FORM_MULTI_SELECT) {
        if (v instanceof Array) {
            w.values = [];
            for (var i = 0; i < v.length; i++) {
                var c = v[i];
                if (typeof (c) === "string") {
                    for (var j = 0; j < w.choices.length; j++) {
                        if (w.choices[j].value === c) {
                            w.values.push(c);
                        }
                    }
                }
            }
        }
    } else if (f.type == FORM_DATE_SELECT) {
        if (typeof (v) == "number") {
            var d = v;
            if ("date" == w.mode) {
                d = d - (d % 86400);
            } else {
                if ("time" == w.mode) {
                    if (d < 0) {
                        d = 0;
                    }
                    if (d > 86400) {
                        d = d % 86400;
                    }
                }
                d = d - (d % (w.minute_interval * 60));
            }
            w.has_date = true;
            w.date = d;
        }

    } else if (f.type == FORM_SINGLE_SLIDER) {
        if (typeof (v) == "number") {
            if (w.min <= v && v <= w.max) {
                w.value = v;
            }
        }

    } else if (f.type == FORM_RANGE_SLIDER) {
        if (v instanceof Array) {
            if (v.length == 2) {
                if (typeof (v[0]) == "number" && typeof (v[1]) == "number") {
                    var vMin = v[0];
                    var vMax = v[1];
                    if (w.min <= vMin && vMin < vMax && vMax <= w.max) {
                        w.low_value = vMin;
                        w.high_value = vMax;
                    }
                }
            }
        }
    } else if (f.type === FORM_ADVANCED_ORDER) {
        if (v.categories) {
            for (var i = 0, categoryCount = w.categories.length; i < categoryCount; i++) {
                var category = w.categories[i];
                var flowCodeCategory = v.categories[category.id];
                if (flowCodeCategory && flowCodeCategory.items) {
                    for (var j = 0, itemCount = category.items.length; j < itemCount; j++) {
                        var item = category.items[j];
                        var flowCodeItem = flowCodeCategory.items[item.id];
                        if (flowCodeItem) {
                            mergeObjects(flowCodeItem, item);
                        }
                    }
                }
            }
        }
    } else if (f.type === FORM_PAY) {
        mergeObjects(v, w);
    }
}

function processMessageStep(state, messageDef, newKey) {
    var timestamp = now();
    var context = state.run.context || null;
    var parentKey = (state.run.parent_message_key == newKey) ? null : state.run.parent_message_key;
    var action = messageDef.getAction(parentKey, newKey, state.run.sender, state.member, context, timestamp);
    // add translation to validation code
    if (messageDef.message_type == MESSAGE_TYPE_FORM) {
        var form = action.request.form_message.form;
        if (form.javascript_validation) {
            form.javascript_validation = addTranslationToCode(form.javascript_validation, true);
        }
    }

    var actionRequest = action.request[messageDef.message_type == MESSAGE_TYPE_FORM ? 'form_message' : 'message'];
    if (state.run.flowCode !== undefined && state.run.flowCode !== null) {
        if (state.run.steps.length == state.run.flowCode.stepCount) {
            if (state.run.flowCode.message && typeof state.run.flowCode.message === 'string') {
                actionRequest.message = state.run.flowCode.message;
            }
            if (messageDef.message_type == MESSAGE_TYPE_MESSAGE) {
                setAnswers(state, action);
            } else if (messageDef.message_type == MESSAGE_TYPE_FORM) {
                setDefaultValue(state, action);
                setFormSettings(state, action);
            }
            if (state.run.flowCode.attachments) {
                actionRequest.attachments = state.run.flowCode.attachments;
            }
        }
    }
    actionRequest.message = getNextStepMessage(actionRequest.message, state);

    state.run.steps.push({
        message_key : newKey,
        step_id : messageDef.id,
        step_type : messageDef.message_type,
        received_timestamp : timestamp,
        message: actionRequest.message
    });

    return createIncomingJsonCall(action.func, action.request);
}

function getNextStepMessage(originalMessage, state) {
    return replaceParams(originalMessage, getFlowcodeLocals(state));
}

/**
 * Finds parameters in a string and attempts to replace them. Defaults to empty string if value not found.
 *
 * Should do roughly the same as lodash template
 * _.templateSettings.interpolate = /{{([\s\S]+?)}}/g;
 * var compiled = _.template(text);
 * return compiled(parameters);
 *
 * @param text{string} text with parameters (e.g. {{ rogerthat.user.name }}
 * @param parameters{object}
 */
function replaceParams(text, parameters) {
    var re = /{{([\s\S]+?)}}/g;
    var groups = text.match(re);

    if (groups) {
        for (var i = 0; i < groups.length; i++) {
            var param = groups[i];  // {{ param }};
            var dotNotation = param.replace('{{', '').replace('}}', '').trim();
            var paramValue = DotObject(dotNotation, parameters);
            if (typeof paramValue !== 'string') {
                paramValue = JSON.stringify(paramValue);
            }
            text = text.replace(param, paramValue);
        }
    }
    return text;
}

function getNextStepDefinitionAndProcessAnswer(state, userInput, serverActions) {
    var messageKey = userInput.request.message_key;
    var buttonId = userInput.request.button_id;
    var currentStep = null;
    for (var i in state.run.steps) {
        if (state.run.steps[i].message_key == messageKey) {
            currentStep = state.run.steps[i];
            break;
        }
    }
    azzert(currentStep, "No step found with message_key " + messageKey + " in state.run");

    var currentMsgDef = flowDefinition[currentStep.step_id];
    azzert(currentMsgDef.step_type == STEP_TYPE_MESSAGE, "Expected nextStep to be of type '" + STEP_TYPE_MESSAGE
        + "', got '" + currentMsgDef.step_type + "'");

    currentStep.answer_id = buttonId;
    currentStep.acknowledged_timestamp = userInput.request.timestamp;

    var messageTO;
    var formResultTO = null;
    var currentAction = currentMsgDef.getAction(userInput.request.parent_message_key, messageKey, state.run.sender,
        state.member, null, currentStep.received_timestamp);
    if (currentMsgDef.message_type == MESSAGE_TYPE_FORM) {
        messageTO = currentAction.request.form_message;
        if (buttonId == FORM_POSITIVE)
            formResultTO = {
                type: WIDGET_RESULT_MAP[messageTO.form.type],
                result: userInput.request.result
            };
        currentStep.form_result = formResultTO;
        currentStep.form_type = messageTO.form.type;
        currentStep.display_value = getFormDisplayValue(messageTO, currentStep.form_result);
        currentStep.button = messageTO.form[buttonId == FORM_POSITIVE ? 'positive_button' : 'negative_button'];
    } else {
        messageTO = currentAction.request.message;
        if (buttonId === null) {
            currentStep.button = ROGERTHAT_BUTTON_CAPTION;
        } else {
            for (var j in messageTO.buttons) {
                if (messageTO.buttons[j].id == buttonId) {
                    currentStep.button = messageTO.buttons[j].caption;
                    break;
                }
            }
        }
    }
    messageTO.message = getNextStepMessage(messageTO.message, state);

    var memberTO = messageTO.member || messageTO.members[0];
    memberTO.status = 7; /* RECEIVED + READ + ACKED */
    memberTO.received_timestamp = currentStep.received_timestamp;
    memberTO.acked_timestamp = currentStep.acknowledged_timestamp;
    memberTO.button_id = buttonId;

    serverActions.push(createIncomingJsonCall(API_NEW_FLOW_MESSAGE, {
        message: messageTO,
        form_result: formResultTO,
        message_flow_run_id: state.run.message_flow_run_id,
        step_id: currentMsgDef.id
    }));

    return flowDefinition[buttonId ? currentMsgDef.button_references[buttonId] : currentMsgDef.dismiss_reference];
}

function getStartDefinition(state, userInput, threadKey, serverActions) {
    if (!state.run.message_flow_run_id)
        state.run.message_flow_run_id = '_js_' + GUID();
    state.run.parent_message_key = threadKey;
    state.run.context = userInput.request.context || flowDefinition.context;
    state.run.sender = userInput.request[userInput.func == API_START_SVC_ACTION ? 'email' : 'service'];
    if (userInput.func == API_PRESS_MENU_ICON) {
        state.run.hashed_tag = userInput.request.hashed_tag;
    } else if (userInput.func == API_START_SVC_ACTION) {
        state.run.service_action = userInput.request.action;
    }
    state.run.steps = [];
    state.static_flow_hash = userInput.request.static_flow_hash;
    userInput.request.message_flow_run_id = state.run.message_flow_run_id;

    serverActions.push(createIncomingJsonCall(userInput.func, userInput.request));

    return flowDefinition[flowDefinition.start];
}

function transition(version, state, input, timeDiff) {
    if (timeDiff !== undefined) {
        adjustedTimeDiff = timeDiff;
    }
    var versionArray = version.split(".");
    var majorVersion = versionArray[0];
    var minorVersion = versionArray[1];
    var buildVersion = versionArray[2];
    var platformVersion = versionArray[3];
    if (platformVersion == 'A') {
        state = typeof (state) == "string" ? JSON.parse(state) : state;
        input = typeof (input) == "string" ? JSON.parse(input) : input;
    }

    if (!state.run)
        state.run = {};
    if (state.message_flow_run_id)
        state.run.message_flow_run_id = state.message_flow_run_id;
    state.run.flow_params = state.flow_params;

    if (!state.userState)
        state.userState = {};

    if (state.user === undefined)
        state.user = {};
    if (state.service === undefined)
        state.service = {};
    if (state.system === undefined)
        state.system = {};

    var nextMsgKey = '_js_' + GUID();

    var serverActions = [];
    var localActions = [];

    var nextStepDef;
    if ([API_PRESS_MENU_ICON, API_START_SVC_ACTION, API_FLOW_STARTED].indexOf(input.func) > -1) {
        var threadKey;
        if (API_FLOW_STARTED == input.func) {
            threadKey = input.request.thread_key;
            if (!flowDefinition.parent_message_key)
                nextMsgKey = threadKey;
        } else {
            threadKey = nextMsgKey;
        }

        nextStepDef = getStartDefinition(state, input, threadKey, serverActions);
    } else {
        nextStepDef = getNextStepDefinitionAndProcessAnswer(state, input, serverActions);
    }
    azzert(nextStepDef, "No next step found");

    while (nextStepDef.step_type == STEP_TYPE_FLUSH || nextStepDef.step_type == STEP_TYPE_EMAIL
    || nextStepDef.step_type == STEP_TYPE_FLOW_CODE) {
        if (nextStepDef.step_type == STEP_TYPE_FLUSH) {
            serverActions.push(processResultsFlush(state, nextStepDef));
            nextStepDef = flowDefinition[nextStepDef.reference];
        } else if (nextStepDef.step_type == STEP_TYPE_EMAIL) {
            serverActions.push(processResultsEmail(state, nextStepDef));
            nextStepDef = flowDefinition[nextStepDef.reference];
        } else {
            nextStepDef = flowDefinition[processFlowCode(state, nextStepDef, localActions, serverActions)];
        }
    }

    if (nextStepDef.step_type == STEP_TYPE_END) {
        processEndStep(state, nextStepDef, localActions, serverActions);
    } else if (nextStepDef.step_type == STEP_TYPE_MESSAGE) {
        localActions.push(processMessageStep(state, nextStepDef, nextMsgKey));
    } else {
        azzert(false, "Can not process step with type " + nextStepDef.step_type);
    }

    return {
        newstate: state,
        local_actions: localActions,
        server_actions: serverActions
    };
}

/* **************************************** */

function now() {
    return Math.round((new Date().getTime() + adjustedTimeDiff) / 1000);
}

function GUID() {
    var S4 = function () {
        return Math.floor(Math.random() * 0x10000 /* 65536 */
        ).toString(16);
    };

    return (S4() + S4() + "-" + S4() + "-" + S4() + "-" + S4() + "-" + S4() + S4() + S4());
}

function cloneObj(obj) {
    /* Handle the 3 simple types, and null or undefined */
    if (null === obj || "object" !== typeof obj)
        return obj;

    /* Handle Date */
    if (obj instanceof Date) {
        return new Date(obj.getTime());
    }

    /* Handle Array */
    if (obj instanceof Array) {
        var copy = [];
        for (var i = 0, len = obj.length; i < len; i++) {
            copy[i] = cloneObj(obj[i]);
        }
        return copy;
    }

    /* Handle Object */
    if (obj instanceof Object) {
        var copy = {};
        for (var attr in obj) {
            if (obj.hasOwnProperty(attr))
                copy[attr] = cloneObj(obj[attr]);
        }
        return copy;
    }

    throw new Error("Unable to copy obj! Its type isn't supported.");
}

function azzert(condition, message) {
    if (!condition) {
        throw new Error(message || "Unknown exception occurred");
    }
}

function getStackTrace(e, isAndroid) {
    if (isAndroid) {
        var stack = (e.stack + '\n').replace(/^\S[^\(]+?[\n$]/gm, '').replace(/^\s+(at eval )?at\s+/gm, '').replace(
            /^([^\(]+?)([\n$])/gm, '{anonymous}()@$1$2').replace(/^Object.<anonymous>\s*\(([^\)]+)\)/gm,
            '{anonymous}()@$1').split('\n');
        stack.pop();
        return stack.join('\n');
    } else {
        return e.stack.replace(/\[native code\]\n/m, '').replace(/^(?=\w+Error\:).*$\n/m, '').replace(/^@/gm,
            '{anonymous}()@');
    }
}

/**
 * Severely stripped down / modified version of DotObject#pick https://github.com/rhalff/dot-object
 */

function parsePath(path, sep) {
    if (path.indexOf('[') >= 0) {
        path = path.replace(/\[/g, '.').replace(/]/g, '');
    }
    return path.split(sep);
}

function parseKey(key, val) {
    // detect negative index notation
    if (key[0] === '-' && Array.isArray(val) && /^-\d+$/.test(key)) {
        return val.length + parseInt(key, 10);
    }
    return key;
}

function DotObject(path, obj) {
    var i, keys, key;
    keys = parsePath(path, '.');
    for (i = 0; i < keys.length; i++) {
        key = parseKey(keys[i], obj);
        if (obj && typeof obj === 'object' && key in obj) {
            if (i === (keys.length - 1)) {
                return obj[key];
            } else {
                obj = obj[key];
            }
        } else {
            return undefined;
        }
    }
    return obj;
}

/* **************************************** */

function mc_run(func, arg_list) {
    var v = arg_list[0];

    var versionArray = v.split(".");
    var platformVersion = versionArray[3];

    var isAndroid = platformVersion == 'A';

    var r = {};
    try {
        /* "this" will be null in the called function */
        var the_result = func.apply(null, arg_list);
        r['success'] = true;
        r['result'] = the_result;
    } catch (err) {
        r['success'] = false;
        r['errname'] = err.name;
        r['errmessage'] = err.message;
        r['errstack'] = getStackTrace(err, isAndroid);
    }

    if (returnScriptable)
        return r;

    return JSON.stringify(r);
}

function mc_run_ext(func) {
    var arg_list = [];
    for (var i = 1; i < arguments.length; i++)
        arg_list.push(arguments[i]);
    return mc_run(func, arg_list);
}
