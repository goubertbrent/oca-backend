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

window.onload = function() {
    if (typeof rogerthat === 'undefined') {
        document.body.innerHTML = GroupPurchaseTranslations.ROGERTHAT_FUNCTION_UNSUPPORTED_UPDATE;
        return;
    }

    $(document).ready(function() {
        rogerthat.callbacks.ready(onRogerthatReady);

        var textColorTag = $("meta[property='rt:style:text-color']")[0];
        var textColor = "#000";
        if(textColorTag !== undefined){
            textColor = textColorTag.content;
        }
        console.log("textColor: " + textColor);

        var backgroundColorTag = $("meta[property='rt:style:background-color']")[0];
        var backgroundColor = "#fff";
        if(backgroundColorTag !== undefined){
            backgroundColor = backgroundColorTag.content;
        }
        console.log("backgroundColor: " + backgroundColor);

        $(".ui-overlay-a, .ui-page-theme-a, .ui-page-theme-a .ui-panel-wrapper").css("background-color", backgroundColor).css("color", textColor).css("text-shadow", "none");
    });
};

var groupPurchases = null;
var groupPurchasesDict = {};

var padLeft = function(string, length, char) {
    string = string + '';
    while (string.length < length) {
        string = char + string;
    }
    return string;
};

var filter = function (array, callback) {
    var result = [];
    for ( var index in array ) {
        if (callback(array[index], index)) {
            result.push(array[index]);
        }
    }
    return result;
};

var hidePopupOverlay = function() {
    $("#gp-popup").popup("close"); // needs to be double for first close
    $("#gp-popup").popup("close");
};

var showPopupOverlay = function(html) {
    $("#gp-popup-content").html(html);
    $("#gp-popup").popup("open", {positionTo: 'window'});
    $('[data-role="page"]').trigger('create');
};

var onRogerthatReady = function() {
    console.log("onRogerthatReady()");
    rogerthat.api.callbacks.resultReceived(onReceivedApiResult);
    
    rogerthat.callbacks.userDataUpdated(loadGroupPurchases);
    rogerthat.callbacks.serviceDataUpdated(loadGroupPurchases);

    loadGroupPurchases();

    $(document).on("click", ".closePopupOverlay", function() {
        hidePopupOverlay();
    });

    $(document).on("click", ".purchaseGroupPurchase", function() {
        var group_purchase_id = $(this).attr("group_purchase_id");
        var group_purchase = groupPurchasesDict[parseInt(group_purchase_id)];

        var units = $("#groupPurchaseUnits").val();
        var units_f = parseInt(units);
        if (isNaN(units_f)) {
            showPopupOverlay(GroupPurchaseTranslations.UNITS_IS_AN_INVALID_NUMBER);
            return;
        }

        if (units_f <= 0) {
            showPopupOverlay(GroupPurchaseTranslations.YOU_NEED_TO_SUBSCRIBE_FOR_AT_LEAST_1_UNIT);
            return;
        }

        if (group_purchase.max_units_pp && (units_f > group_purchase.max_units_pp)) {
            showPopupOverlay(GroupPurchaseTranslations.YOU_CAN_ONLY_SUBSCRIBE_FOR_X_UNITS.replace("{0}", group_purchase.max_units_pp));
            return;
        }

        if (units_f > group_purchase.units_available) {
            showPopupOverlay(GroupPurchaseTranslations.YOU_CAN_ONLY_SUBSCRIBE_FOR_X_UNITS.replace("{0}", group_purchase.units_available));
            return;
        }
        
        var subscribed = rogerthat.user.data.groupPurchaseSubscriptions ? rogerthat.user.data.groupPurchaseSubscriptions[group_purchase.id] : undefined;
        if (subscribed === undefined)
            subscribed = 0;

        if (group_purchase.max_units_pp && (subscribed + units_f) > group_purchase.max_units_pp) {
            showPopupOverlay(GroupPurchaseTranslations.YOU_CAN_ONLY_SUBSCRIBE_FOR_X_UNITS.replace("{0}", (group_purchase.max_units_pp - subscribed)));
            return;
        }

        var paramsss = JSON.stringify({
            'groupPurchaseId' : group_purchase_id,
            'units': units_f
        });
        rogerthat.api.call("solutions.group_purchase.purchase", paramsss, "solutions.group_purchase.purchase");

        showPopupOverlay(GroupPurchaseTranslations.GROUP_SUBSCRIPTION_PROCESSING);
    });
};

moment.locale(navigator.languages ? navigator.languages[0] : (navigator.language || navigator.userLanguage));

var parseDateToEventDateTime = function(d) {
    var momentTrans = moment(d).format("LLLL");
    return momentTrans;
};

var htmlize = function(value){
    return $("<div></div>").text(value).html().replace(/\n/g, "<br>");
};

var caseInsensitiveStringSort = function(a, b) {
    var lowerCaseA = a.toLowerCase();
    var lowerCaseB = b.toLowerCase();
    if (lowerCaseA < lowerCaseB)
        return -1;
    if (lowerCaseA > lowerCaseB)
        return 1;
    return 0;
};

var loadGroupPurchases = function(){
    
    var now = (new Date().getTime()) / 1000;
    groupPurchases = filter(rogerthat.service.data.solutionGroupPurchases, function (groupPurchase, i) {
        return now < groupPurchase.time_until;
    });

    groupPurchases.sort(function(a, b) {
        if (now > a.time_until || now > b.time_until) {
            return a.time_until - b.time_until;
        }
        if((a.time_from - b.time_from) != 0)
            return a.time_from - b.time_from;
        if((a.time_until - b.time_until) != 0)
            return a.time_until - b.time_until;
        return caseInsensitiveStringSort(a.title, b.title);
    });

    $.each(groupPurchases, function (i, groupPurchase){
        groupPurchasesDict[groupPurchase.id] = groupPurchase;
    });

    $("#menu").empty(); // in requests

    if (groupPurchases.length == 0){
        $("#menu").append('<h2 id="group_purchases-empty">' + GroupPurchaseTranslations.NO_GROUP_SUBSCRIPTIONS + '</h2>');
        return;
    }
    
    var colorSchemeTag = $("meta[property='rt:style:color-scheme']")[0];
    var colorscheme = "light";
    if(colorSchemeTag !== undefined){
        colorscheme = colorSchemeTag.content;
    }
    console.log("Colorscheme: " + colorscheme);
    
    var now = (new Date().getTime()) / 1000;
    $.each(groupPurchases, function (i, groupPurchase) {
        var time_from_str = parseDateToEventDateTime(new Date(groupPurchase.time_from * 1000));
        var time_until_str = parseDateToEventDateTime(new Date(groupPurchase.time_until * 1000));
        groupPurchase.htmlDescription = htmlize(groupPurchase.description);
        groupPurchase.subscribed = rogerthat.user.data.groupPurchaseSubscriptions ? rogerthat.user.data.groupPurchaseSubscriptions[groupPurchase.id] : undefined;
        if (groupPurchase.subscribed !== undefined) {
            groupPurchase.subscribed_for = GroupPurchaseTranslations.SUBSCRIBED_FOR_X_UNITS.replace("{0}", groupPurchase.subscribed);
        }

        groupPurchase.htmlUnitDescription = htmlize(groupPurchase.unit_description);
        groupPurchase.from_until_str = GroupPurchaseTranslations.SUBSCRIBE_FROM_TILL.replace("{0}", time_from_str).replace("{1}", time_until_str)
        groupPurchase.available_units_left = GroupPurchaseTranslations.UNITS_AVAILABLE_LEFT.replace("{0}", groupPurchase.units_available).replace("{1}", groupPurchase.units)
    });

    var html = $.tmpl(groupPurchasesTemplate, {
        group_purchases : groupPurchases,
        colorscheme : colorscheme,
        currency: rogerthat.service.data.currency
    });

    $("#menu").append(html);
    $('[data-role="page"]').trigger('create');

    $(".purchase_group_purchase").click(function(){
        var group_purchase_id = $(this).attr("group_purchase_id");
        var group_purchase = groupPurchasesDict[parseInt(group_purchase_id)];
        var html = $('<div></div>');
        // validate time
        var now = (new Date().getTime()) / 1000;
        if (now < group_purchase.time_from) {
            html.append($('<h3></h3>').text(GroupPurchaseTranslations.GROUP_PURCHASE_NOT_STARTED_YET));
            showPopupOverlay(html);
            return;
        }
        if (now >= group_purchase.time_until) {
            html.append($('<h3></h3>').text(GroupPurchaseTranslations.GROUP_PURCHASE_ENDED));
            showPopupOverlay(html);
            return;
        }
        // validate max items to buy
        var subscribed = rogerthat.user.data.groupPurchaseSubscriptions ? rogerthat.user.data.groupPurchaseSubscriptions[group_purchase.id] : undefined;
        if (group_purchase.max_units_pp && (subscribed !== undefined && subscribed >= group_purchase.max_units_pp)) {
            html.append($('<h3></h3>').text(GroupPurchaseTranslations.GROUP_PURCHASE_MAX_UNITS_REACHED));
            showPopupOverlay(html);
            return;
        }

        html.append($('<h3></h3>').text(GroupPurchaseTranslations.ENTER_THE_NUMBER_OF_UNITS_YOU_WANT_TO_SUBSCRIBE_FOR));
        html.append($('<p></p>').addClass('price').text(GroupPurchaseTranslations.UNIT_PRICE + ': ' + rogerthat.service.data.currency + '' + group_purchase.unit_price_in_euro));
        html.append($('<p></p>').addClass('units').text(GroupPurchaseTranslations.MAXIMUM + ": " + (group_purchase.max_units_pp ? group_purchase.max_units_pp : group_purchase.units_available)));
        html.append('<input id="groupPurchaseUnits" type="number" value="' + group_purchase.min_units_pp + '" step="1" min="' +
                group_purchase.min_units_pp + '" max="' + (group_purchase.max_units_pp ? group_purchase.max_units_pp : group_purchase.units_available) + '">');
        html.append('<br>');
        html.append('<button data-role="button" data-inline="true" data-theme="b" class="purchaseGroupPurchase clearfix" group_purchase_id="' + group_purchase_id + '"onclick="">' + GroupPurchaseTranslations.SUBSCRIBE + '</button>');

        showPopupOverlay(html);
    });

    $("img.groupPurchasePicture").each(function () {
        var img = $(this);
        $.ajax({
            url: img.attr('datasrc'),
            success: function (data) {
                if (data && data.success) {
                    img.attr('src', data.picture);
                    img.slideDown();
                }
            }
        });
    });
};

var onReceivedApiResult = function(method, result, error, tag) {
    //solutions.group_purchase.purchase
    console.log("onReceivedApiResult");
    console.log("method: " + method);
    console.log("result: " + result);
    console.log("error: " + error);
};

var groupPurchasesTemplate = '{{each(i, m) group_purchases}}'
    + '<div class="groupPurchase {{if i%2==0}} {{if colorscheme=="dark"}} backgoundDark{{/if}} {{if colorscheme=="light"}} backgoundLight{{/if}} {{/if}}">'//
    + '     <h2 class="title">${m.title}</h2>' //
    + '     {{if m.picture}}<img class="groupPurchasePicture" datasrc="${m.picture}" style="display: none;"/>{{/if}}' //
    + '     <p class="description">{{html m.htmlDescription}}</p>' //
    + '     <p class="from-till">${m.from_until_str}</p>' //
    + '     <p class="unit-description">' + GroupPurchaseTranslations.UNIT_DESCRIPTION + ':<br>{{html m.htmlUnitDescription}}</p>'
    + '     <p class="price">' + GroupPurchaseTranslations.UNIT_PRICE + ': ${currency}${m.unit_price_in_euro}</p>' //
    + '     <p class="units">${m.available_units_left}</p>' //
    + '     {{if m.subscribed}}<p class="subscribed">${m.subscribed_for}</p>{{/if}}'
    + '{{if m.units_available}}<a href="#" class="purchase_group_purchase clearfix" data-role="button" data-inline="true" group_purchase_id="${m.id}" onclick="">'
    + GroupPurchaseTranslations.SUBSCRIBE + '</a>{{/if}}'
    + '</div>' //
    + '{{/each}}';
