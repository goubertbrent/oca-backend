/*
 * Copyright 2016 Mobicage NV
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
 * @@license_version:1.1@@
 */

$(function () {
    'use strict';
	var loading=false;
	var solutionInboxMessageSandwichBarOrders = {};
	var solutionInboxMessageSandwichBarRequests = {};
	var sandwichBarOrdersDict = {};

    var STATUS_RECEIVED = 1;
    var STATUS_READY = 2;
    var STATUS_REPLIED = 3;

    LocalCache.sandwich = {
        settings: null
    };
	var showAllOrders = false;
	var sandwichOrders = [];

    modules.sandwich = {
        getSandwichSettings: getSandwichSettings
    };

    init();

    function init() {
        loadSandwichOrders();
        loadSettings();
        updateShowHideSandwichOrders();
    }

    function channelUpdates(data) {
        if (data.type == 'solutions.common.sandwich.orders.update') {
            loadSandwichOrders();
		} else if(data.type === 'solutions.common.sandwich.orders.deleted') {
			deleteSandwichOrder(data.sandwich_id);
		}
    }

	$('#section_settings_sandwich').find('div.bootstrap-timepicker input').timepicker({
        showMeridian : false,
        minuteStep : 15,
        disableFocus : true
    });

    $("#sandwichOrdersShowTodo, #sandwichOrdersShowAll").click(function () {
        showAllOrders = ! showAllOrders;
        updateShowHideSandwichOrders();
    });

	function deleteSandwichOrder(sandwichId) {
		delete sandwichBarOrdersDict[sandwichId];
		var deletedOrder = sandwichOrders.filter(function(order) {
			return order.id === sandwichId;
		})[0];
		sandwichOrders.splice(sandwichOrders.indexOf(deletedOrder), 1);
		renderSandwichOrders();
	}

    function updateShowHideSandwichOrders() {
        $("#sandwichOrdersShowTodo").toggleClass('btn-success', !showAllOrders)
            .html(showAllOrders ? '&nbsp;' : CommonTranslations.TODO);
        $("#sandwichOrdersShowAll").toggleClass('btn-success', showAllOrders)
            .html(showAllOrders ? CommonTranslations.ALL : '&nbsp;');
        renderSandwichOrders();
    }

    function getActionsForOrder(order) {
        var toolbar = $('<div class="btn-toolbar"></div>');
        var group = $('<div class="btn-group"></div>');

        if (order.status == STATUS_RECEIVED) {
            var btnReady = $('<button action="ready" class="btn btn-large btn-success"><i class="icon-ok icon-white"></i></button>').attr("sandwich_id", order.id).click(readySandwichOrderPressed);
            group.append(btnReady);
			var btnDelete = $('<button action="delete" class="btn btn-large btn-warning"><i class="icon-remove icon-white"></i></button>').attr("sandwich_id", order.id).click(deleteSandwichOrderPressed);
			group.append(btnDelete);
        }

        toolbar.append(group);
        return toolbar;
    }

    function loadSandwichOrders() {
        solutionInboxMessageSandwichBarOrders = {};
        sln.call({
            url : "/common/sandwich/orders/load",
            type : "GET",
            success : function(data) {
                $.each(data, function(i, o) {
                    o.date_time = sln.formatDate(o.timestamp, true);
                    if (o.solution_inbox_message_key) {
                        solutionInboxMessageSandwichBarOrders[o.solution_inbox_message_key] = o;
                        if (solutionInboxMessageSandwichBarRequests[o.solution_inbox_message_key]) {
                            sln.setInboxActions(o.solution_inbox_message_key, getActionsForOrder(o));
                            delete solutionInboxMessageSandwichBarRequests[o.solution_inbox_message_key];
                        }
                    }
                    sandwichBarOrdersDict[o.id] = o;
                });
                sandwichOrders = data;
                renderSandwichOrders();
			}
        });
    }

    function renderSandwichOrders() {
		var sandwichesElem = $("#sandwiches");
		var sandwichOrdersTable = sandwichesElem.find("tbody");

		var localSandwichOrders = sandwichOrders.filter(function(order) {
			return showAllOrders ? true : order.status != STATUS_READY;
		}).map(function (o) {
			if (o.takeaway_time) {
				o.takeaway_time_formatted = sln.formatDate(o.takeaway_time);
			}
			return o;
		});

		var html = $.tmpl(templates.sandwiches_list_item, {
            sandwiches : localSandwichOrders,
            STATUS_RECEIVED: STATUS_RECEIVED,
            STATUS_READY: STATUS_READY,
			STATUS_REPLIED: STATUS_REPLIED,
			CURRENCY: CURRENCY,
			t: CommonTranslations
        });
        sandwichOrdersTable.empty().append(html);
		sandwichesElem.find('button[action="reply"]').click(replySandwichOrderPressed);
		sandwichesElem.find('button[action="ready"]').click(readySandwichOrderPressed);
		sandwichesElem.find('button[action="delete"]').click(deleteSandwichOrderPressed);
        $('.sln-sandwich-badge').text(localSandwichOrders.length || '');
        sln.resize_header();
    }

    function replySandwichOrderPressed() {
        var sandwichId = $(this).attr("sandwich_id");
		var m = sandwichOrders.filter(function(order) {
			return order.id === sandwichId;
		})[0];

        var orderString = $.tmpl(templates.sandwiches_order_inbox_detail, {
            type : m.type,
            topping: m.topping,
            options: m.options,
            remark: m.remark,
            CommonTranslations : CommonTranslations
        });

        sln.inputBox(function(message) {
            sln.call({
                url : "/common/sandwich/orders/reply",
                type : "POST",
                data : {
                    data : JSON.stringify({
                        sandwich_id : sandwichId,
                        message : message
                    })
                },
                success : function(data) {
                    if (!data.success) {
                        return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    }
                },
                error : sln.showAjaxError
            });
        },
        CommonTranslations.REPLY, CommonTranslations.REPLY,
        CommonTranslations.NAME + ": " + m.sender_name, CommonTranslations.NO_MORE_SANDWICHES,
        orderString, null, true);
    }

    function readySandwichOrderPressed(event) {
        event.stopPropagation();
        var sandwichId = $(this).attr("sandwich_id");
        var m = sandwichBarOrdersDict[sandwichId];

        sln.inputBox(function(message, btn) {
            var msg = message;
            if (btn == 2) {
                msg = "";
            }
            sln.call({
                url : "/common/sandwich/orders/ready",
                type : "POST",
                data : {
                    data : JSON.stringify({
                        sandwich_id : sandwichId,
                        message : msg
                    })
                },
                success : function(data) {
                    if (!data.success) {
                        return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    }
                    fadeOutMessageAndUpdateBadge(sandwichId);
                    sln.setInboxActions(m.solution_inbox_message_key, undefined);
                }
            });
        },
        CommonTranslations.READY, CommonTranslations.READY, null,
        CommonTranslations.REPLY_ORDER_READY, null, CommonTranslations.dont_send_message);
    }

    function deleteSandwichOrderPressed(event) {
        event.stopPropagation();
        var sandwichId = $(this).attr("sandwich_id");
        var m = sandwichBarOrdersDict[sandwichId];

        // should reply if not already replied
        var replyRequired, replyMessage = '', placeholder = '';
        replyRequired = (m.status != STATUS_REPLIED);
        if(replyRequired) {
            replyMessage = CommonTranslations.REPLY_ORDER_CANCEL;
        } else {
            placeholder = CommonTranslations.optional_message;
        }

        sln.inputBox(function(message, btn) {
            var msg = message;
            if (btn == 2) {
                msg = "";
            }
            sln.call({
                url : "/common/sandwich/orders/delete",
                type : "POST",
                data : {
                    data : JSON.stringify({
                        sandwich_id : sandwichId,
                        message : msg
                    })
                },
                success : function(data) {
                    if (!data.success) {
                        return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                    }
                    fadeOutMessageAndUpdateBadge(sandwichId);
                    delete solutionInboxMessageSandwichBarOrders[m.solution_inbox_message_key];
                    sln.setInboxActions(m.solution_inbox_message_key, undefined);
                }
            });
        },
        CommonTranslations.DELETE, CommonTranslations.DELETE, null,
        replyMessage, null, null,
        replyRequired, placeholder);
    }

    function fadeOutMessageAndUpdateBadge(sandwichId) {
        $('#sandwiches tr[sandwich_id="' + sandwichId + '"]').fadeOut('slow', function() {
            $(this).remove();
        });
        var badge = $('.sln-sandwich-badge');
        var newBadgeValue = badge.text() - 1;
        badge.text(newBadgeValue > 0 ? newBadgeValue : '');
        sln.resize_header();
    }

    function getSandwichSettings(callback) {
        if (LocalCache.sandwich.settings) {
            callback(LocalCache.sandwich.settings);
        } else {
            loadSettings(callback);
        }
    }

    function loadSettings(callback) {
		loading = true;
		var data = {};
		sln.call({
            url: '/common/sandwich/settings/load',
			data: data,
			success: function (data) {
                LocalCache.sandwich.settings = data;
                setSandwichSettingsEvents(data);
				loading = false;
				if (callback)
                    callback(LocalCache.sandwich.settings);
            }
		});
    }

    function setSandwichSettingsEvents(settings) {
        updateShowHideSandwichPrices();
        $.each([1, 2, 4, 8, 16, 32, 64], function (i, val) {
            $("#sandwiches_available_days input[value=" + val + "]").prop('checked', (settings.days & val) == val);
        });
        $("#sandwich_order_from").timepicker('setTime', sln.intToTime(settings.from_));
        $("#sandwich_order_till").timepicker('setTime', sln.intToTime(settings.till));
        $.each([1, 2, 4, 8, 16, 32, 64], function (i, val) {
            $("#sandwiches_broadcast_days input[value=" + val + "]").prop('checked', (settings.reminder_days & val) == val);
            if (!$("#sandwiches_available_days input[value=" + val + "]").prop('checked'))
                $("#sandwiches_broadcast_days input[value=" + val + "]").prop('disabled', true);
        });
        $("#sandwich_broadcast_at").timepicker('setTime', sln.intToTime(settings.reminder_at));
        $("#sandwich_order_reminder_broadcast_message").val(settings.reminder_message);
        var leapTimeEnabledElem = $('#sandwich_order_leaptime_enabled');
        var leapTimeElem = $('#sandwich_order_leaptime');
        var leapTimeContainer = $('#leap_time_enabled');
        leapTimeElem.val(settings.leap_time);
        leapTimeContainer.toggle(settings.leap_time_enabled);
        leapTimeEnabledElem.prop('checked', settings.leap_time_enabled);
        leapTimeEnabledElem.change(function () {
            var enabled = $(this).prop('checked');
            saveSettings({leap_time_enabled: enabled});
            leapTimeContainer.slideToggle(enabled);
        });
        sln.configureDelayedInput(leapTimeElem, function (value) {
            saveSettings({leap_time: parseInt(value) || 15});
        });
        updateTypesToppingsOptions('types');
        updateTypesToppingsOptions('toppings');
        updateTypesToppingsOptions('options');
    }


	$("#sandwiches_available_days input[type=checkbox]").change(function () {
		var checkbox = $(this);
		var val = parseInt(checkbox.val());
		var reminder_checkbox = $("#sandwiches_broadcast_days input[value="+val+"]");
		if (! checkbox.prop('checked')) {
            LocalCache.sandwich.settings.days = LocalCache.sandwich.settings.days & ~val;
            LocalCache.sandwich.settings.reminder_days = LocalCache.sandwich.settings.reminder_days & ~val;
			reminder_checkbox.prop('checked', false).prop('disabled', true);
		} else {
            LocalCache.sandwich.settings.days = LocalCache.sandwich.settings.days | val;
			reminder_checkbox.prop('disabled', false);
		}
        var data = {days: LocalCache.sandwich.settings.days, reminder_days: LocalCache.sandwich.settings.reminder_days};
		saveSettings(data);
	});

    $("#sandwiches_broadcast_days input[type=checkbox]").change(function () {
		var checkbox = $(this);
		var val = parseInt(checkbox.val());
		if (! checkbox.prop('checked')) {
            LocalCache.sandwich.settings.reminder_days = LocalCache.sandwich.settings.reminder_days & ~val;
		} else {
            LocalCache.sandwich.settings.reminder_days = LocalCache.sandwich.settings.reminder_days | val;
		}
        var data = {reminder_days: LocalCache.sandwich.settings.reminder_days};
		saveSettings(data);
	});

    var from_ = 0;
	$('#sandwich_order_from').on('changeTime.timepicker', function (e) {
		if (loading)
			return;
		from_ = 3600 * e.time.hours;
		from_ += 60 * e.time.minutes;
		$(this).keyup();
	});
    sln.configureDelayedInput($('#sandwich_order_from'), function () {
		var data = {from_: from_};
		saveSettings(data);
    });

    var till = 0;
	$('#sandwich_order_till').on('changeTime.timepicker', function (e) {
		if (loading)
			return;
		till = 3600 * e.time.hours;
		till += 60 * e.time.minutes;
		$(this).keyup();
	});
    sln.configureDelayedInput($('#sandwich_order_till'), function () {
		var data = {till: till};
		saveSettings(data);
    });

	var at = 0;
	$('#sandwich_broadcast_at').on('changeTime.timepicker', function (e) {
		if (loading)
			return;
		at = 3600 * e.time.hours;
		at += 60 * e.time.minutes;
		$(this).keyup();
	});
    sln.configureDelayedInput($('#sandwich_broadcast_at'), function () {
		var data = {reminder_at: at};
		saveSettings(data);
    });

    sln.configureDelayedInput($('#sandwich_order_reminder_broadcast_message'), function () {
		var data = {reminder_message: $('#sandwich_order_reminder_broadcast_message').val()};
		saveSettings(data);
    });

    $("#sandwichHidePrices, #sandwichShowPrices").click(function () {
        LocalCache.sandwich.settings.show_prices = !LocalCache.sandwich.settings.show_prices;
		updateShowHideSandwichPrices();
        saveSettings({show_prices: LocalCache.sandwich.settings.show_prices});
		$(this).blur();
	});

    function updateShowHideSandwichPrices() {
        if (LocalCache.sandwich.settings.show_prices) {
			$("#sandwichHidePrices").html('&nbsp;');
            $("#sandwichShowPrices").addClass('btn-success').text(CommonTranslations.SHOW_PRICES);
		} else {
			$("#sandwichHidePrices").text(CommonTranslations.HIDE_PRICES);
			$("#sandwichShowPrices").removeClass('btn-success').html('&nbsp;');
		}
    }

    function updateTypesToppingsOptions(kind) {
		var body = $("fieldset.sandwich-"+kind+" tbody");
		var newBody = $('<tbody></tbody>');
		var template = $("#sandwichSettingItemTemplate tbody tr");
		function compare(a,b) {
			if (a.order < b.order)
				return -1;
			if (a.order > b.order)
				return 1;
			return 0;
		}

        var items = LocalCache.sandwich.settings[kind].sort(compare);
		$.each(items, function (i, item) {
			var tr = template.clone();
			$("td.sandwich-description", tr).text(item.description);
            $("td.sandwich-price", tr).text(LocalCache.sandwich.settings.currency + " " + (item.price / 100).toFixed(2));
			tr.data('item', item);
			if ( i == 0 )
				$("a.move-up", tr).addClass('disabled');
			else
				$("a.move-up", tr).click(function () {
					var this_tr = $(this).closest('tr');
					var this_item = this_tr.data('item');
					var up_item = items[items.indexOf(this_item)-1];
					var up_item_order = up_item.order;
					up_item.order = this_item.order;
					this_item.order = up_item_order;
					updateTypesToppingsOptions(kind);
					var data = {};
					data[kind] = [this_item, up_item];
					saveSettings(data);
				});
			if ( i == items.length - 1 )
				$("a.move-down", tr).addClass('disabled');
			else
				$("a.move-down", tr).click(function () {
					var this_tr = $(this).closest('tr');
					var this_item = this_tr.data('item');
					var down_item = items[items.indexOf(this_item)+1];
					var down_item_order = down_item.order;
					down_item.order = this_item.order;
					this_item.order = down_item_order;
					updateTypesToppingsOptions(kind);
					var data = {};
					data[kind] = [this_item, down_item];
					saveSettings(data);
				});
			$('a.trash', tr).click(function () {
				var this_tr = $(this).closest('tr');
				var this_item = this_tr.data('item');
				this_item.deleted = true;
				var data = {};
				data[kind] = [this_item];
				saveSettings(data);
                LocalCache.sandwich.settings[kind].splice(LocalCache.sandwich.settings[kind].indexOf(this_item), 1);
				updateTypesToppingsOptions(kind);
			});
			$('a.edit', tr).click(function () {
				var this_tr = $(this).closest('tr');
				var this_item = this_tr.data('item');
				var modal = $("#add_edit_sandwich_item").attr('mode', 'edit');
				$("div.modal-header h3", modal).text(this_item.description);
				$("#sandwich_item_description", modal).val(this_item.description);
				$("#sandwich_item_price", modal).val((this_item.price / 100).toFixed(2));
				$("#add_edit_sandwich_item_error").hide();
				modal.attr('item-kind', kind);
				modal.data('item', this_item);
				modal.modal('show');
			});
			newBody.append(tr);
		});
		var st = $(document).scrollTop();
		body.replaceWith(newBody);
		$(document).scrollTop(st);
    }

    function saveSettings(updatedSettings, callback, errback) {
	    sln.call({
            url: '/common/sandwich/settings/save',
			type: 'POST',
			data: {
				data: JSON.stringify({
                    sandwich_settings: updatedSettings
				})
			},
            success: function (data) {
				if (callback)
                    callback(data);
			},
			error : errback ? errback : sln.showAjaxError
		});
    }

	$("button.add_sandwich_item").click(function () {
		var button = $(this);
		var modal = $("#add_edit_sandwich_item").attr('mode', 'add');
		$("div.modal-header h3", modal).text(button.text());
		$("#sandwich_item_description", modal).val('');
		$("#sandwich_item_price", modal).val('0');
		$("#add_edit_sandwich_item_error").hide();
		modal.attr('item-kind', button.attr('item-kind'));
		modal.data('item', null);
		modal.modal('show');
	});

	$("#button_save_sandwich_item").click(function () {
		var modal = $("#add_edit_sandwich_item");
		var description = $("#sandwich_item_description", modal).val().trim();
		var price = parseFloat($("#sandwich_item_price", modal).val());
		if (! description) {
			$("#add_edit_sandwich_item_error span", modal).text(CommonTranslations.DESCRIPTION_IS_REQUIRED);
			return;
		}
		if (isNaN(price)) {
			price = 0;
		}
		var kind = modal.attr('item-kind');
		var data = {};
		if (modal.attr('mode') == 'add') {
            var items = LocalCache.sandwich.settings[kind];
			var order = 0;
			$.each(items, function (i, item) { order = Math.max(order, item.order); });
			data[kind] = [{description: description, price: Math.round(price*100), order: order+1}];
			sln.showProcessing(CommonTranslations.SAVING_DOT_DOT_DOT);
            saveSettings(data, function (updatedSettings) {
                sln.hideProcessing();
				modal.modal('hide');
                LocalCache.sandwich.settings = updatedSettings;
                updateTypesToppingsOptions(kind);
			}, function (err) {
				sln.hideProcessing();
                sln.showAjaxError(err);
			});
		} else {
			var this_item = modal.data('item');
			this_item.description = description;
			this_item.price = Math.round(price*100);
			data[kind] = [this_item];
			saveSettings(data);
			modal.modal('hide');
			updateTypesToppingsOptions(kind);
		}
	});

	sln.registerMsgCallback(channelUpdates);

    sln.registerInboxActionListener("sandwich_bar", function (chatId) {
        var o = solutionInboxMessageSandwichBarOrders[chatId];
        if (o) {
            sln.setInboxActions(o.solution_inbox_message_key, getActionsForOrder(o));
        } else {
            solutionInboxMessageSandwichBarRequests[chatId] = chatId;
        }
    });
});
