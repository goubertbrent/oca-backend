/*
 * Copyright 2017 GIG Technology NV
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

var LOYALTY_TYPE_REVENUE_DISCOUNT = 1;
var LOYALTY_TYPE_LOTTERY = 2;
var LOYALTY_TYPE_STAMPS = 3;

var visits = null;
var x_visits = 10;
var x_discount = 5;
var x_stamps = 8;
var stamps_winnings = "";
var solutionsLoyaltyLotteryChanceGuid = null;

window.onload = function() {
    if (typeof rogerthat === 'undefined') {
        document.body.innerHTML = Translations.ROGERTHAT_FUNCTION_UNSUPPORTED_UPDATE;
        return;
    }

    $(document).ready(function() {
        rogerthat.callbacks.ready(onRogerthatReady);
    });
};

var htmlize = function(value) {
    return $("<div></div>").text(value).html().replace(/\n/g, "<br>");
};

var onRogerthatReady = function() {
    console.log("onRogerthatReady()");
    console.log("OSA Loyalty USER v1.0.5");
    console.log("LOYALTY_TYPE: " + LOYALTY_TYPE);
    var language = window.navigator.languages ? window.navigator.languages[0] : null;
    language = language || window.navigator.language || window.navigator.browserLanguage
            || window.navigator.userLanguage;
    console.log("Language: " + language);
    moment.locale(language);
    
    var onReceivedApiResult = function(method, result, error, tag){
        console.log("onReceivedApiResult");
        console.log("method: " + method);
        console.log("result: " + result);
        console.log("error: " + error);
        console.log("tag: " + tag);
        
        if (method == "solutions.loyalty.lottery.chance") {
            if (solutionsLoyaltyLotteryChanceGuid == null || tag == null) {
                return;
            }
            
            if (tag == solutionsLoyaltyLotteryChanceGuid) {
                solutionsLoyaltyLotteryChanceGuid = null;
                if (result) {
                    var r = JSON.parse(result);
                    $("#lottery-total").html(htmlize(Translations.LOTTERY_TEXT_DISCOUNT.replace("%%", "%").replace("%(count)s", r.my_visits).replace("%(chance)s", (r.chance).toFixed(2))));
                }
            }
        }
    };
    
    rogerthat.api.callbacks.resultReceived(onReceivedApiResult);

    rogerthat.callbacks.serviceDataUpdated(function() {
        console.log("rogerthat.callbacks.serviceDataUpdated");
        initRogerthatData();
        loadLoyalty();
    });

    rogerthat.callbacks.userDataUpdated(function() {
        console.log("rogerthat.callbacks.userDataUpdated");
        initRogerthatData();
        loadLoyalty();
    });
    
    initRogerthatData();
    loadLoyalty();
};

var initRogerthatData = function() {
    // SERVICE
    if(rogerthat.service.data == null) {
        rogerthat.service.data = {};
    }
    if(rogerthat.service.data.loyalty == undefined) {
        rogerthat.service.data.loyalty = {};
    }
    if (rogerthat.service.data.loyalty.settings != undefined) {
        if (rogerthat.service.data.loyalty.settings.x_visits != null) {
            x_visits = rogerthat.service.data.loyalty.settings.x_visits;
        }
        if (rogerthat.service.data.loyalty.settings.x_discount != null) {
            x_discount = rogerthat.service.data.loyalty.settings.x_discount;
        }
    }
    if(rogerthat.service.data.loyalty_2 == undefined) {
        rogerthat.service.data.loyalty_2 = {};
    }
    if(rogerthat.service.data.loyalty_2.dates == undefined) {
        rogerthat.service.data.loyalty_2.dates = [];
    }
    
    if (rogerthat.service.data.loyalty_3 != undefined) {
        if (rogerthat.service.data.loyalty_3.settings != undefined) {
            if (rogerthat.service.data.loyalty_3.settings.x_stamps != undefined) {
                x_stamps = rogerthat.service.data.loyalty_3.settings.x_stamps;
            }
            if (rogerthat.service.data.loyalty_3.settings.stamps_winnings != undefined) {
                stamps_winnings = rogerthat.service.data.loyalty_3.settings.stamps_winnings;
            }
        }
    }
    
    // USER
    if (rogerthat.user.data == null) {
        rogerthat.user.data = {};
    }
    if (rogerthat.user.data.loyalty == undefined) {
        rogerthat.user.data.loyalty = {}
    }
    if (rogerthat.user.data.loyalty.visits == undefined) {
        rogerthat.user.data.loyalty.visits = [];
    }
    if (rogerthat.user.data.loyalty_3 == undefined) {
        rogerthat.user.data.loyalty_3 = {}
    }
    if (rogerthat.user.data.loyalty_3.visits == undefined) {
        rogerthat.user.data.loyalty_3.visits = [];
    }
};

var parseDateToDateTime = function(d) {
    var momentTrans = moment(d).format("LLLL");
    return momentTrans;
};

var priceToString = function(cents) {
    var currency = rogerthat.service.data.currency || "";
    return currency + (cents / 100.0).toFixed(2);
};

var createListItem = function(indexString, txt) {
    var li = $('<li data-role="list-divider" role="heading" class="ui-li ui-li-divider ui-bar-a ui-li-has-count"></li>');
    var p = $('<p></p>').css('font-size', '1em');
    var strong = $('<strong style="float: left; margin-right: 1em;"></strong>');
    strong.text(indexString);
    p.append(strong);
    var div = $('<div></div>');
    div.text("  " + txt);
    p.append(div);
    li.append(p);
    return li;
};

var createVisitListItem = function(indexString, visit) {
    var li = $('<li data-role="list-divider" role="heading" class="ui-li ui-li-divider ui-bar-a ui-li-has-count"></li>');
    if (visit == null) {
        li.text(indexString);
    } else {
        var d = new Date(visit.timestamp * 1000);
        var time = parseDateToDateTime(d);
        var p = $('<p></p>').css('font-size', '1em');
        var strong = $('<strong style="float: left; margin-right: 1em;"></strong>');
        strong.text(indexString);
        p.append(strong);
        var div = $('<div></div>');
        div.text("  " + time);
        p.append(div);
        li.append(p);
        var span = $('<span class="ui-li-count ui-btn-up-c ui-btn-corner-all"></span>');
        span.text(priceToString(visit.value_number));
        li.append(span);
    }
    return li;
};

var createVisitCard = function(hasTopMargin) {
    var d_ = $('<div class="ui-grid-b"></div>');
    if (hasTopMargin) {
        d_.css("margin-top", "0.5em");
    }
    return d_;
};

var createVisitCardItem = function(index, file_name, opacity, clazz) {
    var d_ = $('<div></div>');
    if (index % 3 == 0) {
        d_.addClass("ui-block-a");
    } else if (index % 3 == 1) {
        d_.addClass("ui-block-b");
    } else if (index % 3 == 2) {
        d_.addClass("ui-block-c");
    }
    
    if (clazz) {
        d_.addClass(clazz);
        if (clazz == "gotoPrice") {
            $(d_).on("click", function() {
                $.mobile.changePage( "#price", { transition: "slideup"} );
            });
        }
    }
    
    var d_1 = $('<div class="ui-bar ui-bar-a" style="text-align: center; padding: 1em 0 0.6em 0; background-color: transparent;"></div>');
    var d_1_img = $('<img class="stamp" style="width: 100%; max-width: 50px; height: auto;">');
    d_1_img.attr("src", file_name);
    d_1_img.css("opacity", opacity);
    d_1.append(d_1_img);
    d_.append(d_1);
    return d_;
};

var getNextLottery = function() {
    rogerthat.service.data.loyalty_2.dates.sort(function(a, b) {
        var dA = new Date(a.date.year, a.date.month - 1, a.date.day, a.date.hour, a.date.minute);
        var dB = new Date(b.date.year, b.date.month - 1, b.date.day, b.date.hour, b.date.minute);
        return dA - dB;
    });
    
    var now_ = Math.floor(Date.now() / 1000);
    for (var i in rogerthat.service.data.loyalty_2.dates) {
        var d = rogerthat.service.data.loyalty_2.dates[i];
        var ld = new Date(d.date.year, d.date.month - 1, d.date.day, d.date.hour, d.date.minute);
        if (now_ <= ld.getTime() / 1000) {
            d.datetime = ld;
            return d;
        }
    }
    return null;
};

var loadLoyalty = function() {
    if (LOYALTY_TYPE == LOYALTY_TYPE_REVENUE_DISCOUNT) {
        loadLoyaltyRevenueDiscount();
    } else if (LOYALTY_TYPE == LOYALTY_TYPE_LOTTERY) {
        loadLoyaltyLottery();
    } else {
        loadLoyaltyStamps();
    }
};

var loadLoyaltyRevenueDiscount = function() {
    visits = rogerthat.user.data.loyalty.visits;
    var listView = $("#visits-listview").empty();
    console.log("x_visits: " + x_visits);
    console.log("x_discount: " + x_discount);
    
    var totalPrice = 0;
    var rows = x_visits > visits.length ? x_visits: visits.length;
    for (i = 0; i < rows; i++) {
        var visit = null;
        if (visits.length > i) {
            visit = visits[visits.length - i - 1];
            totalPrice += visit.value_number;
        }
        var indexString = "" + ((i % x_visits) + 1);
        listView.append(createVisitListItem(indexString, visit));
    }
    
    var discount = Math.round(totalPrice * x_discount) / 100;
    
    $("#visits-total").text(
            Translations.REDEEM_TEXT_DISCOUNT.replace("{0}", x_discount + '%').replace("{1}", priceToString(totalPrice))
            .replace("{2}", priceToString(discount)));
};

var loadLoyaltyLottery = function() {
    var lottery = getNextLottery();
    
    if (lottery == null) {
        $(".no_upcoming").show();
        $(".has_upcoming").hide();
        return;
    }
    $(".no_upcoming").hide();
    $(".has_upcoming").show();
    
    
    $("#lottery-end").text(parseDateToDateTime(lottery.datetime));
    $("#lottery-winnings").html(htmlize(lottery.winnings));
    
    var userDetails = {};
    userDetails.language = rogerthat.user.language;
    userDetails.avatar_url = rogerthat.user.avatarUrl;
    userDetails.email = rogerthat.user.account;
    userDetails.name = rogerthat.user.name;
    userDetails.app_id = rogerthat.system.appId;
    
    solutionsLoyaltyLotteryChanceGuid = rogerthat.util.uuid();
    
    rogerthat.api.call("solutions.loyalty.lottery.chance", 
            JSON.stringify({
                     'loyalty_type': LOYALTY_TYPE,
                     'timestamp': Math.floor(Date.now() / 1000),
                     'user_details': userDetails
             }),
             solutionsLoyaltyLotteryChanceGuid);
};

var loadLoyaltyStamps = function() {
    visits = rogerthat.user.data.loyalty_3.visits;
    var cardsHolder = $("#visits-card-holder").empty();
    console.log("x_stamps: " + x_stamps);
    
    var count = 0;
    $.each(visits, function (i, visit) {
        count += visit.value_number;
    });
    
    var fullCards = parseInt(count / x_stamps);
    var stampsLeft = count % x_stamps; 
    
    console.log("got " + fullCards + " full cards to redeem");
    console.log("got " + stampsLeft + " stamps on new card");
    
    var totalCount = 0;
    var index = 0;
    var card = createVisitCard(false);
    for (i = 0; i < fullCards; i++) {
        for (ii = 0; ii < x_stamps; ii++) {
            card.append(createVisitCardItem(index, "loyalty_stamps_visit.png", 1));
            index += 1;
        }
        card.append(createVisitCardItem(index, "loyalty_stamps_gift.png", 1, "gotoPrice"));
        index = 0;
        
        cardsHolder.append(card);
        card = createVisitCard(true);
    }
    
    for (i = 0; i < x_stamps; i++) {
        if (i + 1 > stampsLeft) {
            card.append(createVisitCardItem(index, "loyalty_stamps_visit.png", 0.2));
            index += 1;
        } else {
            card.append(createVisitCardItem(index, "loyalty_stamps_visit.png", 1));
            index += 1;
        }
    }
    if (count > 0 && stampsLeft == 0) {
        card.append(createVisitCardItem(index, "loyalty_stamps_gift.png", 1, "gotoPrice"));
    } else {
        card.append(createVisitCardItem(index, "loyalty_stamps_gift.png", 0.2, "gotoPrice"));
    }
    cardsHolder.append(card);
};

$(document).on("click", ".gotoPrice", function() {
    console.log(".gotoPrice");
    $("#price .price-description p").html(htmlize(stamps_winnings));
});
