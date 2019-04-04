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

var NEWS_TYPE_NORMAL = 1, NEWS_TYPE_QR = 2;

function NewsWizard(newsList, options) {
    this.newsList = newsList;
    this.tag = newsList.tag;
    this.options = options || {};
    this.keepState = false;

    this.serviceMenu = this.options.serviceMenu || {};
    this.broadcastOptions = this.options.broadcastOptions;
    this.appStatistics = this.options.appStatistics;
    this.menu = null;  // loaded when editing / adding news
    this.sandwichSettings = this.options.sandwichSettings;
    this.initialData = null;

    this.newsTypes = {
        1: T('normal'),
        2: T('coupon')
    };

    this.title = options.title || T('news_items');

    // default steps
    this.steps = options.steps || [{
        text: T('news_type'),
        description: T('news_type_explanation'),
        tab: 0,
    }, {
        text: T('Content'),
        description: T('news_content_explanation'),
        tab: 1,
    }, {
        text: T('image_optional'),
        description: T('news_image_explanation'),
        tab: 2,
    }, {
        text: T('Label'),
        description: T('news_label_explanation'),
        tab: 3,
    }, {
        text: T('action_button'),
        description: T('news_action_button_explanation'),
        type: NEWS_TYPE_NORMAL,
        tab: 4,
    }, {
        text: T('delayed_broadcast'),
        description: T('news_schedule_explanation'),
        tab: 5,
    }, {
        text: T('target_audience'),
        description: T('news_target_audience_explanation'),
        tab: 6,
    }, {
        text: T('checkout'),
        description: '',
        tab: 7
    }];

    this.validation = {
        rules: {
            news_checkbox_apps: {
                required: true
            }
        },
        errorPlacement: function (error, element) {
            if (element.attr('name') === 'news_checkbox_apps') {
                error.insertAfter($(element).parent().parent());
            } else {
                error.insertAfter(element);
            }
        }
    };
    this.defaultButtons = options.defaultButtons || [{
        label: T('like'),
    }, {
        label: T('follow')
    }];

    this.translations = options.translations || {
        item_saved: 'news_item_saved',
        item_published: 'news_item_published',
        item_scheduled: 'news_item_scheduled_for_datetime',
        item_publish_error: 'could_not_publish_newsitem',
    };

    this.promotedNews = {};
    modules.broadcast.registerAttachmentUploadedHandler(this.attachmentUploaded.bind(this));
}

NewsWizard.prototype = {

    getAllowedButtonActions: function () {
        var allowedButtonActions = [{
            value: 'url',
            type: 'url',
            translation: T('WEBSITE'),
            defaultLabel: T('open_website')
        }, {
            value: 'phone',
            type: 'tel',
            translation: T('phone_number'),
            defaultLabel: T('Call')
        }, {
            value: 'email',
            type: 'email',
            translation: T('email_address'),
            defaultLabel: T('send_email')
        }, {
            value: 'attachment',
            type: 'url',
            translation: T('Attachment'),
            defaultLabel: T('Attachment')
        }];
        if (MODULES.includes('joyn')) {
            allowedButtonActions.push({
                value: 'joyn_coupon',
                type: 'url',
                translation: T('joyn-coupon'),
                defaultLabel: T('activate')
            });
        }
        return allowedButtonActions;
    },
    edit: function (newsId, initialData) {
        this.initialData = initialData;
        newsId = parseInt(newsId);
        var newsItem;
        if (newsId) {
            if (this.newsList.isEmpty()) {
                return this.goToOverview();
            }
            newsItem = this.newsList.getItem(newsId);
        }
        if (this.serviceMenu) {
            this.render(newsItem);
        }
    },

    goToOverview: function () {
        window.location.hash = this.newsList.baseLink + '/overview';
    },

    goToShop: function () {
        window.location.hash = '#/shop';
    },

    getActionButtonValue: function (actionButton) {
        if (!actionButton) {
            return '';
        }
        if (actionButton.id === 'url') {
            return actionButton.action;
        }
        if (actionButton.id === 'joyn_coupon') {
            var params = JSON.parse(actionButton.action.split('open://')[1]);
            return params.original_url;
        }
        return actionButton.action.split('://')[1];
    },


    isPresentInApp: function (app_id) {
        return ACTIVE_APPS.indexOf(app_id) !== -1;
    },

    getCityAppTotalReach: function (appIds) {
        return this.appStatistics.reduce(function (result, app) {
            if (appIds.indexOf(app.app_id) !== -1) {
                return result + app.total_user_count;
            }
            return result;
        }, 0);
    },

    freeRegionalNews: function () {
        var tags = this.broadcastOptions.news_settings.tags || [];
        return tags.indexOf(CONSTS.NEWS_TAGS.FREE_REGIONAL_NEWS) > -1;
    },

    showBudget: function () {
        var self = this;
        if (self.freeRegionalNews()) {
            self.$('#news_current_budget').text(CommonTranslations.unlimited);
            self.$('#news_views').hide();
        } else {
            Requests.getBudget().then(function (budget) {
                self.$('#news_current_budget').text(budget.balance * CONSTS.BUDGET_RATE);
                self.$('#news_views').show();
            });
        }
    },

    attachmentUploaded: function (url, name) {
        // set the attachment name and trigger a keyup
        // to re-render the preview
        this.$('#news_action_attachment_caption').val(name);
        this.$('#news_action_attachment_caption').keyup();
        // set the attachment value/url
        this.$('#news_action_attachment_value').val(url);
        // hide the add button and show remove button
        this.$('#news_action_remove_attachment').show();
        this.$('#news_action_add_attachment').hide();
    },

    render: function (newsItem) {
        var actionButtonId, actionButton, actionButtonLabel, flowParams, restaurantReservationDate, selectedSandwich,
            actionButtonValue;
        restaurantReservationDate = new Date().getTime() / 1000;
        if (!newsItem && this.initialData) {
            newsItem = this.initialData;
        }
        var promotionProduct = this.broadcastOptions.news_promotion_product;
        actionButton = newsItem ? newsItem.buttons[0] : null;
        actionButtonId = actionButton ? actionButton.id : null;
        actionButtonValue = this.getActionButtonValue(actionButton);
        actionButtonLabel = actionButton ? actionButton.caption : '';
        this.citySelect = null;
        var appIds, apps;
        if (newsItem && newsItem.id) {
            apps = [];
            appIds = newsItem.app_ids;
            for (var appName in CONSTS.CITY_APPS) {
                if (appIds.indexOf(CONSTS.CITY_APPS[appName]) !== -1) {
                    apps.push({
                        name: appName,
                        id: CONSTS.CITY_APPS[appName]
                    });
                }
            }
        } else {
            // default app
            apps = [ALL_APPS[0]];
            appIds = [ALL_APPS[0].id];
        }
        this.apps = apps;
        this.appIds = appIds;

        var totalReach = this.getCityAppTotalReach(appIds);
        if (actionButton) {
            try {
                flowParams = JSON.parse(actionButton.flow_params);
            } catch (e) {
                console.error(e);
            }
        }
        if (flowParams) {
            if (flowParams.advancedOrder && flowParams.advancedOrder.categories && this.menu) {
                for (var i = 0; i < this.menu.categories.length; i++) {
                    var category = this.menu.categories[i],
                        flowParamCategory = flowParams.advancedOrder.categories[category.id];
                    if (flowParamCategory) {
                        for (var j = 0; j < category.items.length; j++) {
                            var item = category.items[j],
                                flowParamItem = flowParamCategory.items[item.id];
                            if (flowParamItem) {
                                item.selectedAmount = flowParamItem.value;
                            }
                        }
                    }
                }
            } else if (flowParams.reservationDate) {
                restaurantReservationDate = flowParams.reservationDate;
            } else if (flowParams.sandwichType) {
                selectedSandwich = {
                    type: flowParams.sandwichType,
                    topping: flowParams.sandwichTopping,
                    options: flowParams.sandwichOptions
                };
            }
        }
        actionButton = {
            id: actionButtonId,
            value: actionButtonValue,
            label: actionButtonLabel
        };
        var self = this;
        Requests.getSettings().then(function (settings) {
            var params = {
                T: T,
                serviceMenu: self.serviceMenu,
                canSendNewsItem: self.broadcastOptions.next_news_item_time * 1000 < new Date().getTime(),
                nextNewsItemTime: self.broadcastOptions.next_news_item_time,
                broadcastTypes: self.broadcastOptions.editable_broadcast_types,
                promotionProduct: self.broadcastOptions.news_promotion_product,
                regionalNewsEnabled: self.broadcastOptions.regional_news_enabled,
                product_counts_labels: promotionProduct.possible_counts.map(function (c) {
                    return T('days_amount', {amount: c});
                }),
                product_prices: promotionProduct.possible_counts.map(function (c) {
                    return LEGAL_ENTITY_CURRENCY + ' ' + (c * promotionProduct.price / 100);
                }),
                newsItem: newsItem || {
                    type: NEWS_TYPE_NORMAL
                },
                actionButton: actionButton,
                newsTypes: self.newsTypes,
                apps: apps,
                stats: self.getCityAppStats(),
                totalReach: totalReach,
                menu: self.menu,
                UNIT_SYMBOLS: UNIT_SYMBOLS,
                UNITS: UNITS,
                CURRENCY: CONSTS.CURRENCY_SYMBOLS[settings.currency],
                CONSTS: CONSTS,
                CommonTranslations: CommonTranslations,
                restaurantReservationDate: restaurantReservationDate,
                sandwichSettings: self.sandwichSettings,
                selectedSandwich: selectedSandwich || {},
                isFlagSet: sln.isFlagSet,
                allowedButtonActions: self.getAllowedButtonActions(),
                roles: self.broadcastOptions.roles,
                baseLink: self.newsList.baseLink,
                title: self.title,
                hasMap: !!CONSTS.MAP_FILE,
            };
            var html = $.tmpl(templates['broadcast/broadcast_news'], params);
            self.newsList.container.html(html);
            self.setupEventHandlers(newsItem && newsItem.id ? newsItem : null);
        });
    },

    $: function (selector) {
        return this.newsList.getElement(selector);
    },

    getCityAppStats: function () {
        if (!this.appStats) {
            this.appStats = this.appStatistics.reduce(function (result, app) {
                result[app.app_id] = app.total_user_count;
                return result;
            }, {});
        }
        return this.appStats;
    },

    setupEventHandlers: function (originalNewsItem) {
        var self = this;

        var elemRadioNewsType = self.$('input[name=news_select_type]'),
            elemInputTitle = self.$('#news_input_title'),
            elemInputMessage = self.$('#news_input_message'),
            elemSelectBroadcastType = self.$('#news_select_broadcast_type'),
            elemInputImage = self.$('#news_input_image'),
            elemInputUseCoverPhoto = self.$('#news_button_cover_photo'),
            elemSelectButton = self.$('#select_broadcast_button'),
            elemNewsButtonContainer = self.$('#news_button_container'),
            elemButtonCaption = self.$('#news_button_caption'),
            elemCheckboxPromote = self.$('#checkbox_promote'),
            elemImagePreview = self.$('#news_image_preview'),
            elemImageEditorContainer = self.$('#news_image_editor_container'),
            elemButtonRemoveImage = self.$('#news_button_remove_image'),
            elemButtonSaveImage = self.$('#news_button_save_image'),
            elemButtonSubmit = self.$('#news_submit'),
            elemButtonPrevious = self.$('#news_back'),
            elemButtonNext = self.$('#news_next'),
            elemForm = self.$('#form_broadcast_news'),
            elemNewsFormContainer = self.$('#news_form_container'),
            elemStepTitle = self.$('#step_title'),
            elemStepDescription = self.$('#step_content_explanation'),
            elemNewsPreview = self.$('#news_preview'),
            elemNewsActionOrder = self.$('#news_action_order'),
            elemNewsActionAddAttachment = self.$('#news_action_add_attachment'),
            elemNewsActionRemoveAttachment = self.$('#news_action_remove_attachment'),
            elemNewsActionAttachmentCaption = self.$('#news_action_attachment_caption'),
            elemNewsActionAttachmentValue = self.$('#news_action_attachment_value'),
            elemCheckboxesApps = elemForm.find('input[name=news_checkbox_apps]'),
            elemEditCityApps = elemForm.find('#edit_city_apps'),
            elemCheckboxesRoles = elemForm.find('#roles').find('input[type=checkbox]'),
            elemNewsActionRestaurantDatepicker = self.$('#news_action_restaurant_reservation_datepicker'),
            elemNewsActionRestaurantTimepicker = self.$('#news_action_restaurant_reservation_timepicker'),
            elemNewsActionSandwichType = self.$('#news_action_sandwich_bar_types'),
            elemNewsActionSandwichTopping = self.$('#news_action_sandwich_bar_toppings'),
            elemNewsActionSandwichOptions = $('input[name=news_action_sandwich_bar_options]'),
            elemCheckboxSchedule = self.$('#news_send_later'),
            elemInputScheduleDate = self.$('#news_scheduled_at_date'),
            elemInputScheduleTime = self.$('#news_scheduled_at_time'),
            elemScheduledAtError = self.$('#news_scheduled_at_error'),
            elemInputActionButtonUrl = self.$('#news_action_url_value'),
            elemCheckPostToFacebook = self.$('#post_to_facebook'),
            elemCheckPostToTwitter = self.$('#post_to_twitter'),
            elemBroadcastOnTwitter = $("#broadcast_message_on_twitter").find("input"),
            elemFacebookPage = self.$('#facebook_page'),
            elemConfigureTargetAudience = self.$('#configure_target_audience'),
            restaurantReservationDate;

        var itemIsPublished = originalNewsItem && originalNewsItem.published;

        elemButtonSaveImage.hide();
        elemButtonRemoveImage.toggle(!(!originalNewsItem || !originalNewsItem.media));
        elemButtonSubmit.hide();

        var renderPreview = sln.debounce(doRenderPreview, 250);
        elemCheckboxPromote.change(paidContentChanged);
        elemButtonSubmit.click(function (e) {
            newsFormSubmitted(e, !originalNewsItem || !originalNewsItem.id);
        });
        elemInputImage.change(imageChanged);
        elemInputUseCoverPhoto.click(useCoverPhoto);
        elemButtonRemoveImage.click(removeImage);
        elemForm.on('change', 'input[name=news_checkbox_apps]', cityAppsChanged);
        elemEditCityApps.click(editCityApps);
        elemCheckboxSchedule.change(scheduleChanged);
        elemButtonPrevious.click(previousStep);
        elemButtonNext.click(nextStep);
        // Prepares the form for validation
        elemForm.validate(self.validation);

        elemRadioNewsType.change(newsTypeChanged);
        elemSelectBroadcastType.change(renderPreview);
        elemSelectButton.change(actionButtonChanged);
        elemInputTitle.on('input paste keyup', renderPreview);
        elemButtonCaption.on('input paste keyup', renderPreview);

        elemInputActionButtonUrl.keyup(actionButtonUrlChanged);

        elemNewsActionAddAttachment.click(modules.broadcast.addAttachment);
        elemNewsActionRemoveAttachment.click(removeAttachment);

        restaurantReservationDate = new Date(parseInt(elemNewsActionRestaurantDatepicker.attr('data-date')) * 1000);
        elemNewsActionRestaurantDatepicker.datepicker({
            format: sln.getLocalDateFormat(),
            startDate: restaurantReservationDate.toLocaleDateString()
        }).datepicker('setValue', restaurantReservationDate);
        elemNewsActionRestaurantTimepicker.timepicker({
            showMeridian: false
        }).timepicker('setTime', restaurantReservationDate.getHours() + ':' + restaurantReservationDate.getMinutes());
        var scheduleDate;
        if (originalNewsItem && originalNewsItem.scheduled_at !== 0) {
            scheduleDate = new Date(originalNewsItem.scheduled_at * 1000);
        } else {
            scheduleDate = new Date();
            scheduleDate.setDate(scheduleDate.getDate() + 1);
            scheduleDate.setHours(scheduleDate.getHours() - 1);
            scheduleDate.setMinutes(0);
        }
        elemInputScheduleDate.datepicker({
            format: sln.getLocalDateFormat()
        }).datepicker('setValue', scheduleDate);
        elemInputScheduleDate.parent().find('span').click(function () {
            if (!elemInputScheduleDate.attr('disabled')) {
                elemInputScheduleDate.datepicker('show');
            }
        });

        elemCheckPostToFacebook.change(checkForFacebookLogin);
        elemCheckPostToTwitter.change(checkForTwitterLogin);
        var messageEditor = new SimpleMDE({
            autoDownloadFontAwesome: false,
            element: elemInputMessage[0],
            initialValue: originalNewsItem && originalNewsItem.message,
            spellChecker: false,
            status: false,
            toolbar: ['bold', 'italic', 'strikethrough', 'unordered-list', 'link'],
        });

        messageEditor.codemirror.on('change', function () {
            renderPreview();
        });

        function plusClick(elem) {
            return function () {
                elem.val(parseInt(elem.val()) + 1);
            };
        }

        function minClick(elem) {
            return function () {
                var value = parseInt(elem.val());
                elem.val(value > 0 ? value - 1 : 0);
            };
        }

        self.$('#age_max_plus').click(plusClick(self.$('#age_max')));
        self.$('#age_min_plus').click(plusClick(self.$('#age_min')));
        self.$('#age_max_min').click(minClick(self.$('#age_max')));
        self.$('#age_min_min').click(minClick(self.$('#age_min')));

        var checboxLocalNews = self.$('#checkbox_local_news');
        checboxLocalNews.click(function () {
            if (self.citySelect) {
                var defaultApp = self.apps[0];
                self.citySelect.setSelection(defaultApp.name, checboxLocalNews.is(':checked'));
            } else {
                renderPreview();
            }
        });

        self.$('#checkbox_regional_news').click(function () {
            var mustShow = $(this).is(':checked');
            self.$('#regional_news').toggle(mustShow);
            if (self.citySelect) {
                if (mustShow) {
                    self.citySelect.renderPreview();
                    renderPreview();
                }
            } else {
                initAppSelect(function () {
                    var selectDefaultApp = checboxLocalNews.is(':checked');
                    self.citySelect.setSelection(self.apps[0].name, selectDefaultApp);
                });
            }
        });

        self.$('#regional_news a[data-toggle="tooltip"]').tooltip();
        self.$('#charge_budget').click(goToBudgetProduct);

        elemConfigureTargetAudience.change(configureTargetAudience);

        function configureTargetAudience() {
            if (elemConfigureTargetAudience.is(':checked')) {
                self.$('#target_audience').show();
            } else {
                self.$('#target_audience').hide();
            }
        }

        function checkFacebookPermissions(permissionsList) {
            var errors = [];

            if (permissionsList.indexOf('manage_pages') === -1 ||
                permissionsList.indexOf('publish_pages') === -1) {
                errors.push(T('facebook-manage-pages-required'));
            }

            if (errors.length > 0) {
                sln.alert(errors.join('<br/>'));
                return false;
            } else {
                return true;
            }
        }

        function loginToFacebook() {
            FB.login(function (response) {
                    if (response && response.authResponse) {
                        if (checkFacebookPermissions(response.authResponse.grantedScopes)) {
                            loadFacebookPages(response.authResponse.accessToken);
                        } else {
                            elemCheckPostToFacebook.attr('checked', false);
                        }
                    } else {
                        elemCheckPostToFacebook.attr('checked', false);
                    }
                    sln.hideProcessing();
                },
                {
                    scope: 'manage_pages,publish_pages',
                    return_scopes: true
                });
        }

        function checkForFacebookLogin() {
            if (elemCheckPostToFacebook.is(':checked')) {
                sln.showProcessing(CommonTranslations.LOADING_DOT_DOT_DOT);
                loginToFacebook();
            } else {
                elemFacebookPage.hide();
            }
        }

        function checkForTwitterLogin() {
            if (elemCheckPostToTwitter.is(':checked')) {
                var userName = elemBroadcastOnTwitter.val();
                if (!userName) {
                    sln.alert(CommonTranslations.TWITTER_PAGE_REQUIRED);
                    elemCheckPostToTwitter.attr('checked', false);
                }
            }
        }

        function loadFacebookPages(userAccessToken) {
            elemFacebookPage.html('');
            var param = '/me/accounts?access_token=' + userAccessToken;
            FB.api(param, function (response) {
                if (!response || response.error) {
                    elemCheckPostToFacebook.attr('checked', false);
                    return;
                }
                $.each(response.data, function (i, page) {
                    if (page.tasks.indexOf('CREATE_CONTENT') > -1) {
                        elemFacebookPage.append($('<option>', {text: page.name, value: page.access_token}));
                    }
                });
                elemFacebookPage.show();
                sln.hideProcessing();
            });
        }

        elemInputScheduleTime.timepicker({
            showMeridian: false
        }).timepicker('setTime', scheduleDate.getHours() + ':' + scheduleDate.getMinutes());
        currentStep = 0;
        stepChanged(getNewsFormData());
        cityAppsChanged();

        if (originalNewsItem && originalNewsItem.media) {
            elemImageEditorContainer.show();
        }
        if (originalNewsItem) {
            if (originalNewsItem.published || new Date(originalNewsItem.scheduled_at * 1000) < new Date()) {
                elemInputScheduleDate.prop('disabled', true);
                elemInputScheduleTime.prop('disabled', true);
            }
        }

        function newsTypeChanged() {
            if (!elemInputTitle.val()) {
                elemInputTitle.val(T('news_coupon_default_text', {
                    merchant_name: LocalCache.settings.name
                }));
            }
            renderPreview();
        }

        function actionButtonChanged() {
            Requests.getOrderSettings().then(function (orderSettings) {
                var selectedAction = (elemSelectButton.val() || '').split('.');
                self.$('.news_action').hide();
                var defaultActions = ['url', 'email', 'phone', 'attachment', 'joyn_coupon'];
                var isDefaultAction = defaultActions.includes(selectedAction[0]);
                var defaultButtonText = elemSelectButton.find(':selected').text().trim();
                if (selectedAction[0].startsWith('__sln__') || isDefaultAction) {
                    var showElem = true;
                    if (isDefaultAction) {
                        self.$('#news_action_' + selectedAction[0]).toggle(showElem);
                    } else {
                        if (orderSettings.order_type !== CONSTS.ORDER_TYPE_ADVANCED && selectedAction[1] === 'order') {
                            showElem = false;
                        }
                        self.$('#news_action_' + selectedAction[1]).toggle(showElem);
                    }
                    var action = self.getAllowedButtonActions().find(b => b.value === selectedAction[0]);
                    if (action) {
                        defaultButtonText = action.defaultLabel;
                    }
                } else if (selectedAction[0] === 'reserve1') {
                    self.$('#news_action_restaurant_reservation').show();
                }
                elemButtonCaption.val(defaultButtonText);
                elemButtonCaption.prop('required', !!selectedAction[0]);
                elemNewsButtonContainer.toggle(!!selectedAction[0]);
                renderPreview();
            });
        }

        function actionButtonUrlChanged() {
            var url = elemInputActionButtonUrl.val();
            if (url && !url.startsWith('http://') && !url.startsWith('https://') && url.length > 8) {
                elemInputActionButtonUrl.val('http://' + url);
            }
        }

        function removeAttachment() {
            // reset action button to none and
            elemSelectButton.find('option:eq(0)').prop('selected', 'true');
            // reset the previous values
            elemNewsActionAttachmentValue.val('');
            elemNewsActionAttachmentCaption.val(T('Attachment'));
            // show add button
            elemNewsActionAddAttachment.show();
            elemNewsActionRemoveAttachment.hide();
            // then trigger change event to re-render the preview
            actionButtonChanged();
        }

        function shouldPay(callback) {
            // just disable payments for now
            return callback(false);

            var shouldShowPaymentScreen = false;
            var selectedAppIds = [];
            elemCheckboxesApps.filter(':checked').each(function () {
                selectedAppIds.push(this.value);
            });
            var originalApps = originalNewsItem ? originalNewsItem.app_ids : [];
            for (var i = 0; i < selectedAppIds.length; i++) {
                if (!self.isPresentInApp(selectedAppIds[i])) {
                    shouldShowPaymentScreen = true;
                    break;
                }
            }
            if (!shouldShowPaymentScreen && elemCheckboxPromote.prop('checked')) {
                getPromotedCost(selectedAppIds, true, function (data) {
                    $.each(data, function (i, costInApp) {
                        if (originalApps.indexOf(costInApp.app_id) === -1 && costInApp.remaining_free === 0) {
                            shouldShowPaymentScreen = true;
                        }
                    });
                    callback(shouldShowPaymentScreen);
                });
            } else {
                callback(shouldShowPaymentScreen);
            }
        }

        function paidContentChanged() {
            shouldPay(function (pay) {
                elemButtonNext.toggle(pay);
                elemButtonSubmit.toggle(!pay);
            });
            if (elemCheckboxPromote.prop('checked')) {
                var allAppIds = ALL_APPS.map(function (app) {
                    return app.id;
                });
                getPromotedCost(allAppIds, true, function (promotedCosts) {
                    $.each(promotedCosts, function (i, promotedCost) {
                        if (promotedCost.remaining_free !== 0) {
                            var text = T('x_free_promoted_items_remaining', {amount: promotedCost.remaining_free});
                            self.$('#free_promoted_' + promotedCost.app_id).html('<br />' + text);
                        }
                    });
                });
            } else {
                self.$('.free_promoted_text').empty();
            }
        }

        function getNewsFormData() {
            var data = {
                title: elemInputTitle.val().trim() || '',
                message: messageEditor.value().trim() || '',
                broadcast_type: elemSelectBroadcastType.val().trim(),
                sponsored: elemCheckboxPromote.prop('checked'),
                type: parseInt(elemRadioNewsType.filter(':checked').val()),
                tag: self.tag
            };
            if (elemImagePreview.attr('src')) {
                // update image or leave old image
                if (elemImagePreview.attr('src').indexOf('data:image/jpeg') === 0) {
                    data.image = elemImagePreview.attr('src');
                    data.media = {
                        type: 'image',
                        content: elemImagePreview.attr('src'),
                        height: elemImagePreview.prop('naturalHeight'),
                        width: elemImagePreview.prop('naturalWidth'),
                    };
                }
            } else {
                // delete image
                data.media = null;
            }
            var selectedActionButtonId = elemSelectButton.val() || '';
            if (selectedActionButtonId) {
                var actionPrefix = 'smi',
                    actionValue = selectedActionButtonId;
                switch (selectedActionButtonId) {
                    case 'attachment':
                    case 'url':
                        var url_or_attachment = selectedActionButtonId === 'url' ? 'url' : 'attachment';
                        var elemValue = self.$('#news_action_' + url_or_attachment + '_value');
                        actionValue = elemValue.val();
                        try {
                            var splitAction = actionValue.match(/https?:\/\/(.*)/);
                            var isHttps = splitAction.length ? splitAction[0].indexOf('https') === 0 : false;
                            actionPrefix = isHttps ? 'https' : 'http';
                            actionValue = splitAction[1];
                        } catch (e) {
                            console.info(e);
                            actionValue = elemValue.val();
                            actionPrefix = 'http';
                        }
                        break;
                    case 'email':
                        actionPrefix = 'mailto';
                        actionValue = self.$('#news_action_email_value').val();
                        break;
                    case 'phone':
                        actionPrefix = 'tel';
                        actionValue = self.$('#news_action_phone_value').val();
                        break;
                    case 'joyn_coupon':
                        actionPrefix = 'open';
                        var url = $('#news_action_joyn_coupon_value').val();
                        var scheme = "joyn://collect-coupon/";
                        if (url.startsWith("https://my.acc.joyn")) {
                            scheme = "joyn-acc://collect-coupon/";
                        }
                        scheme += url.split('/collect-coupon/')[1];
                        actionValue = JSON.stringify({
                            original_url: url,
                            action_type: "open",
                            action: "app",
                            android_app_id: "com.thanksys.joyn.user",
                            android_scheme: scheme,
                            ios_app_id: "id1157594279",
                            ios_scheme: scheme
                        });
                        break;
                }
                var actionButton = {
                    id: selectedActionButtonId,
                    caption: elemButtonCaption.val() && elemButtonCaption.val().trim(),
                    action: actionPrefix + '://' + actionValue,
                    flow_params: ''
                };
                var flowParams = {};
                switch (selectedActionButtonId) {
                    case '__sln__.order':
                        /**
                         * Structure
                         *
                         * "categories" : {
                         *     "category-1-uuid":{
                         *         "items:{
                         *             "product-1-uuid":{
                         *                 "value": 50
                         *             }
                         *         }
                         *     }
                         * }
                         **/
                        flowParams.advancedOrder = {};
                        var categories = {};
                        elemNewsActionOrder.find('input').each(function () {
                            var input = $(this);
                            var amount = parseInt(input.val()) || 0;
                            if (amount) {
                                var categoryId = input.data('category');
                                var productId = input.data('product');
                                if (!categories[categoryId]) {
                                    categories[categoryId] = {
                                        items: {}
                                    };
                                }
                                if (!categories[categoryId].items[productId]) {
                                    categories[categoryId].items[productId] = {};
                                }
                                categories[categoryId].items[productId] = {
                                    value: amount
                                };
                            }
                        });
                        flowParams.advancedOrder.categories = categories;
                        break;
                    case '__sln__.sandwich_bar':
                        flowParams.sandwichType = 'type_' + elemNewsActionSandwichType.val();
                        flowParams.sandwichTopping = 'topping_' + elemNewsActionSandwichTopping.val();
                        flowParams.sandwichOptions = [];
                        elemNewsActionSandwichOptions.filter(':checked').each(function () {
                            flowParams.sandwichOptions.push('option_' + this.value);
                        });
                        break;
                    case 'reserve1':
                        if (elemNewsActionRestaurantDatepicker.data('datepicker')) {
                            var date = elemNewsActionRestaurantDatepicker.data('datepicker').date;
                        } else {
                            date = new Date();
                            date.setHours(date.getHours() + 2);
                            date.setMinutes(0);
                        }
                        if (elemNewsActionRestaurantTimepicker.data('timepicker')) {
                            date.setHours(elemNewsActionRestaurantTimepicker.data('timepicker').hour);
                            date.setMinutes(elemNewsActionRestaurantTimepicker.data('timepicker').minute);
                        }
                        flowParams.reservationDate = parseInt(date.getTime() / 1000);
                        break;
                }
                actionButton.flow_params = JSON.stringify(flowParams);
                data.action_button = actionButton;
            }
            if (elemCheckboxSchedule.prop('checked') && !itemIsPublished) {
                var scheduledDate = new Date(elemInputScheduleDate.data('datepicker').date.getTime());
                var time = elemInputScheduleTime.data('timepicker');
                scheduledDate.setHours(time.hour);
                scheduledDate.setMinutes(time.minute);
                data.scheduled_at = parseInt(scheduledDate.getTime() / 1000);
            }

            var newAppIds = [];
            if (!originalNewsItem) {
                if (self.citySelect && self.$('#checkbox_regional_news').is(':checked')) {
                    newAppIds = self.citySelect.getSelectedAppIds();
                    newAppIds = newAppIds.filter(function (n) {
                        return n != null;
                    }); // remove NULL
                } else if (self.$('#checkbox_local_news').is(':checked')) {
                    newAppIds = [ACTIVE_APPS[0]]; // default app
                }
            }
            data.app_ids = newAppIds;

            if (elemCheckPostToFacebook.is(':checked')) {
                data.broadcast_on_facebook = true;
                data.facebook_access_token = elemFacebookPage.val();
            } else {
                data.broadcast_on_facebook = false;
            }

            if (elemCheckPostToTwitter.is(':checked')) {
                data.broadcast_on_twitter = true;
            } else {
                data.broadcast_on_twitter = false;
            }

            if (elemConfigureTargetAudience.is(':checked')) {
                data.target_audience = {
                    min_age: parseInt(self.$('#age_min').val()),
                    max_age: parseInt(self.$('#age_max').val()),
                    gender: parseInt(self.$('#gender').val()),
                    connected_users_only: self.$('#connected_users_only').is(':checked')
                };
            }
            data.role_ids = [];
            elemCheckboxesRoles.filter(':checked').each(function () {
                data.role_ids.push(parseInt($(this).val()));
            });
            return data;
        }

        function newsFormSubmitted(e, isNew) {
            e.preventDefault();
            var data = getNewsFormData();
            // validate the scheduled date/time again
            // as the user may publish after the scheduled date/time has passed
            if (!validateScheduledAt(data)) {
                sln.alert(T('date_must_be_in_future'), null, CommonTranslations.ERROR);
                previousStep();
                return;
            }
            // check for facebook access token even if the post on facebook is checked
            if (!elemCheckPostToFacebook.is(':disabled')) {
                if (data.broadcast_on_facebook && !data.facebook_access_token) {
                    sln.alert(T('Login with facebook first'), null, CommonTranslations.ERROR);
                    return;
                }
            }
            if (data.image) {
                delete data.image;
            }
            submitNews(data, undefined, isNew);
        }

        function getPromotedCost(appIds, promoted, callback) {
            var cacheStr = appIds.sort().join(',');
            if (!promoted || !appIds) {
                callback();
                return;
            } else if (self.promotedNews[cacheStr]) {
                callback(self.promotedNews[cacheStr]);
                return;
            }
            sln.call({
                url: '/common/news/promoted_cost',
                method: 'post',
                data: {
                    app_ids: appIds
                },
                success: function (data) {
                    self.promotedNews[cacheStr] = data;
                    callback(data);
                }
            });
        }

        function pollCCInfo(callback) {
            getCreditCardInfo(function (data) {
                if (!data) {
                    // data not available yet. Try again in 500 ms...
                    console.info('Credit card info not available yet. Retrying...');
                    setTimeout(function () {
                        pollCCInfo(callback);
                    }, 500);
                } else {
                    callback(data);
                }
            });

        }

        function getCreditCardInfo(callback) {
            var options = {
                method: 'get',
                url: '/common/billing/card/info',
                success: callback
            };
            sln.call(options);
        }

        function showNewsOrderPage(data) {
            var checkoutContainer = self.$('#tab7');
            checkoutContainer.html(TMPL_LOADING_SPINNER);
            // apologies for this monstrosity
            getCreditCardInfo(function (creditCardInfo) {
                Requests.getBroadcastOptions().then(function (broadcastOptions) {
                    getPromotedCost(data.app_ids, data.sponsored, function (promotedCostList) {
                        var promotionProduct = broadcastOptions.news_promotion_product,
                            fromDate = new Date(),
                            untilDate = new Date();
                        untilDate.setDate(fromDate.getDate() + 7);
                        var orderItems = [],
                            orderItemNumber = 0;
                        if (data.app_ids) {
                            for (var i = 0; i < data.app_ids.length; i++) {
                                var currentAppId = data.app_ids[i];
                                var appName = ALL_APPS.filter(function (p) {
                                    return p.id === currentAppId;
                                })[0].name;
                                if (data.sponsored) {
                                    var promotedCount = promotedCostList.filter(function (item) {
                                        return item.app_id === currentAppId;
                                    })[0];
                                    var comment;
                                    if (promotedCount.remaining_free > 0) {
                                        if (promotedCount.remaining_free === 1) {
                                            comment = T('this_is_the_last_free_promoted_news_item', {
                                                app_name: appName
                                            });
                                        } else {
                                            // No need to bill for something that is free.
                                            continue;
                                        }
                                    } else {
                                        comment = promotionProduct.default_comment
                                            .replace('%(post_title)s', data.title || data.qr_code_caption)
                                            .replace('%(from_date)s', sln.format(fromDate))
                                            .replace('%(until_date)s', sln.format(untilDate))
                                            .replace('%(app_name)s', appName);
                                    }

                                    var sponsoredOrderItem = {
                                        count: promotedCount.count,
                                        description: promotionProduct.description,
                                        comment: comment,
                                        number: orderItemNumber,
                                        price: promotionProduct.price,
                                        product: promotionProduct.code,
                                        app_id: currentAppId
                                    };
                                    orderItems.push(sponsoredOrderItem);
                                    orderItemNumber++;
                                }
                            }
                        }
                        renderNewsOrderPage(orderItems, creditCardInfo);
                    });
                });
            });

            function renderNewsOrderPage(orderItems, creditCardInfo) {
                if (!creditCardInfo) {
                    creditCardInfo = false;
                }
                var totalExclVat = 0, vat = 0, total = 0;
                $.each(orderItems, function (i, orderItem) {
                    var tot = orderItem.price * orderItem.count / 100;
                    var vatTemp = tot * VAT_PCT / 100;
                    totalExclVat += tot;
                    vat += vatTemp;
                    total += tot + vatTemp;
                });
                var html = $.tmpl(templates['shop/shopping_cart'], {
                    items: orderItems,
                    vatPct: VAT_PCT,
                    totalExclVat: totalExclVat.toFixed(2),
                    vat: vat.toFixed(2),
                    total: total.toFixed(2),
                    checkout: true,
                    creditCard: creditCardInfo,
                    t: CommonTranslations,
                    LEGAL_ENTITY_CURRENCY: LEGAL_ENTITY_CURRENCY,
                    customBackButton: T('back')
                });
                checkoutContainer.html(html);
                checkoutContainer.find('#change-creditcard, #link-cc, #add-creditcard').click(function () {
                    callBackAfterCCLinked = function () {
                        pollCCInfo(function (ccinfo) {
                            creditCardInfo = ccinfo ? ccinfo : false; // when undefined, it shows 'loading'.
                            renderNewsOrderPage(orderItem, creditCardInfo);
                        });
                    };
                    manageCreditCard();
                });
                checkoutContainer.find('#checkout').click(function () {
                    // show loading instead of 'pay with creditcard'
                    var $this = $(this);
                    if ($this.is(':disabled')) {
                        return;
                    }
                    if (creditCardInfo) {
                        loading();
                        submitNews(data, orderItems);
                    } else {
                        callBackAfterCCLinked = function () {
                            pollCCInfo(function (ccinfo) {
                                creditCardInfo = ccinfo ? ccinfo : false; // when undefined, it shows 'loading'.
                                if (creditCardInfo) {
                                    loading();
                                    submitNews(data, orderItems);
                                }
                            });
                        };
                        manageCreditCard();
                    }

                    function loading() {
                        $this.find('.normal').hide();
                        $this.find('.loading').show();
                        $this.attr('disabled', true);
                    }
                });
                checkoutContainer.find('#shopping_cart_back_button').click(previousStep);
            }
        }

        function submitNews(newsItem, orderItems, isNew) {
            if (isNew) {
                if (!newsItem.app_ids.length) {
                    sln.alert(CommonTranslations.select_local_and_or_regional_news, null, CommonTranslations.ERROR);
                    return;
                }
                checkRegionalNewsBudget(function () {
                    publishNews(newsItem, orderItems);
                });
            } else {
                publishNews(newsItem, orderItems);
            }
        }

        function getReviewApps(itemAppIds, publishedAppIds) {
            var reviewApps = [];
            $.each(CONSTS.CITY_APPS, function (appName, appId) {
                if (itemAppIds.indexOf(appId) > -1 && publishedAppIds.indexOf(appId) === -1) {
                    reviewApps.push(appName);
                }
            });
            return reviewApps.join(', ');
        }

        function publishNews(newsItem, orderItems) {
            if (elemButtonSubmit.attr('disabled')) {
                return;
            }
            if (!elemForm.valid()) {
                return;
            }
            orderItems = orderItems || [];
            var data = newsItem;
            data.order_items = orderItems;
            data.news_id = originalNewsItem ? originalNewsItem.id : undefined;
            elemButtonSubmit.attr('disabled', true);

            if (data.scheduled_at > 0) {
                sln.showProcessing(CommonTranslations.LOADING_DOT_DOT_DOT);
            } else {
                sln.showProcessing(CommonTranslations.PUBLISHING_DOT_DOT_DOT);
            }
            sln.call({
                url: '/common/news',
                method: 'post',
                data: data,
                success: function (result) {
                    sln.hideProcessing();
                    if (result.errormsg && !result.success) {
                        sln.alert(result.errormsg, null, CommonTranslations.ERROR);
                        // re-enable the submit button
                        elemButtonSubmit.attr('disabled', false);
                        return;
                    }

                    if (result.warningmsg && !originalNewsItem) {
                        var warning = CommonTranslations[result.warningmsg] || result.warningmsg;
                        return sln.alert(warning, self.goToOverview.bind(self), CommonTranslations.SUCCESS);
                    }

                    self.promotedNews = {};
                    elemButtonSubmit.attr('disabled', false);
                    var text;
                    var reviewApps = newsReviewEnabled & !originalNewsItem ? getReviewApps(newsItem.app_ids, result.app_ids) : '';
                    if (reviewApps) {
                        text = CommonTranslations.news_review_partially_published.replace('%(apps)s', reviewApps);
                    } else if (result.published) {
                        if (originalNewsItem) {
                            text = T(self.translations.item_saved);
                        } else {
                            text = T(self.translations.item_published);
                        }
                    } else {
                        text = T(self.translations.item_scheduled, {
                            datetime: sln.format(new Date(result.scheduled_at * 1000))
                        });
                    }
                    sln.alert(text, self.goToOverview.bind(self), CommonTranslations.SUCCESS);
                    $.each(orderItems, function (i, orderItem) {
                        if (orderItem.app_id) {
                            ACTIVE_APPS.push(orderItem.app_id);
                        }
                    });
                    self.newsList.clear();
                },
                error: function () {
                    sln.hideProcessing();
                    elemButtonSubmit.attr('disabled', false);
                    var btn = self.$('#checkout');
                    btn.find('.normal').hide();
                    btn.find('.loading').show();
                    btn.attr('disabled', true);
                    sln.alert(T(self.translations.item_publish_error));
                }
            });
        }

        function useCoverPhoto() {
            function toDataUrl(src, callback) {
                var img = new Image();
                img.crossOrigin = 'Anonymous';
                img.onload = function () {
                    var canvas = document.createElement('CANVAS');
                    var ctx = canvas.getContext('2d');
                    var dataURL;
                    canvas.height = this.height;
                    canvas.width = this.width;
                    ctx.drawImage(this, 0, 0);
                    dataURL = canvas.toDataURL('image/jpeg');
                    callback(dataURL);
                };
                img.src = src;
                // force onload event for cached images
                if (img.complete || img.complete === undefined) {
                    img.src = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==";
                    img.src = src;
                }
            }

            toDataUrl('/common/settings/my_logo', function (dataUrl) {
                elemImagePreview.attr('src', dataUrl).css({'max-width': 350, height: 131.25});
                elemImagePreview.cropper('destroy');
                elemInputImage.val('');
                elemInputUseCoverPhoto.hide();
                elemButtonSaveImage.hide();
                elemImageEditorContainer.show();
                elemButtonRemoveImage.show();
                renderPreview();
            });
        }

        function removeImage() {
            elemImagePreview.cropper('destroy');
            elemImagePreview.attr('src', '');
            elemInputImage.val('');
            elemImageEditorContainer.hide();
            elemInputUseCoverPhoto.show();
            $('.news_image img').attr('src', '');
            doRenderPreview();
        }

        function imageChanged() {
            var CROP_OPTIONS = {
                viewMode: 1,
                dragMode: 'crop',
                rotatable: true,
                autoCropArea: 1.0,
                minContainerWidth: 480,
                minContainerHeight: 270,
                preview: '.news_image'
            };
            sln.readFile(this, elemImagePreview, 'dataURL', function () {
                self.$('.news_image').show().find('img').remove();
                elemImagePreview.css({'max-width': 480, height: 270});
                elemImagePreview.cropper('destroy');
                elemImagePreview.cropper(CROP_OPTIONS);
                elemImageEditorContainer.show();
                elemButtonRemoveImage.show();
                elemButtonSaveImage.show().unbind('click').click(resizeImage);
                var preview = self.$('.news_image');
                elemImagePreview.off('load').on('load', function () {
                    var height = 480 / elemImagePreview.prop('naturalWidth') * elemImagePreview.prop('naturalHeight');
                    preview.css({height: height});
                });
            });
        }

        function resizeImage(event) {
            if (elemInputImage.get(0).files.length !== 0) {
                var options = {
                    imageSmoothingEnabled: true,
                    imageSmoothingQuality: 'high',
                };
                var data = elemImagePreview.cropper('getData');
                if (data.height > data.width) {
                    options.maxHeight = 1440;
                } else {
                    options.maxWidth = 1440;
                }
                var croppedImageCanvas = elemImagePreview.cropper('getCroppedCanvas', options);
                if (croppedImageCanvas) {
                    var resizedImageDataUrl = croppedImageCanvas.toDataURL('image/jpeg', .85);
                    elemImagePreview.attr('src', resizedImageDataUrl);
                    elemImagePreview.cropper('destroy');
                    elemButtonSaveImage.hide();
                    elemInputImage.val('');
                    if (event) {
                        renderPreview();
                    }
                }
            }
        }

        function cityAppsChanged() {
            var selectedAppIds, defaultApp, defaultAppIsSelected;
            if (self.citySelect) {
                selectedAppIds = self.citySelect.getSelectedAppIds();
            } else {
                selectedAppIds = self.appIds;
            }

            defaultApp = ALL_APPS[0];
            defaultAppIsSelected = selectedAppIds.indexOf(defaultApp.id) > -1;
            if (self.citySelect && self.citySelect.getEnabledApps()[defaultApp.name]) {
                self.$('#checkbox_local_news').prop('checked', defaultAppIsSelected);
            }

            var totalReach = self.getCityAppTotalReach(selectedAppIds);
            var localReach = 0;
            if (defaultAppIsSelected) {
                localReach = self.getCityAppTotalReach(defaultApp.id) || 0;
            }
            self.$('#news_estimated_reach').text(modules.news.getEstimatedReach(totalReach));
            self.$('#news_max_reach').text(totalReach);
            Requests.getSettings().then(function (settings) {
                var currency = CONSTS.CURRENCY_SYMBOLS[settings.currency];
                self.$('#news_estimated_cost').text(modules.news.getEstimatedCost(totalReach - localReach, currency));
                renderPreview();
            });
        }

        function getMapData(mapFile, callback) {
            if (self.mapData) {
                return callback(self.mapData);
            }
            $.getJSON('/static/js/shop/libraries/' + mapFile, function (data) {
                self.mapData = data;
                callback(data);
            });
        }

        function initCitySelect(previewContainer, data) {
            var preselected, stats;
            preselected = self.apps.map(function (app) {
                return app.name;
            });
            stats = self.getCityAppStats();
            Requests.getSettings().then(function (settings) {
                var currency = CONSTS.CURRENCY_SYMBOLS[settings.currency];
                if (data) {
                    self.citySelect = new MapCitySelect(CONSTS.CITY_APPS, stats, preselected, previewContainer, data, true, currency);
                } else {
                    self.citySelect = new ListCitySelect(CONSTS.CITY_APPS, stats, preselected, previewContainer, currency);
                }

                self.citySelect.onSelectionCompleted = cityAppsChanged;
                self.citySelect.setOnSelectClicked(editCityApps);
                self.citySelect.setOnDefaultClicked(editCityApps);
                if (originalNewsItem) {
                    self.citySelect.lockPreview();
                }
            });
        }

        function initAppSelect(callback) {
            if (self.citySelect) {
                return;
            }

            if (!callback) {
                callback = function () {
                };
            }

            var mapFile = CONSTS.MAP_FILE;
            var previewContainer = self.$('#app_select_preview');
            if (mapFile) {
                previewContainer.append(TMPL_LOADING_SPINNER);
                elemButtonSubmit.attr('disabled', true);
                getMapData(mapFile, function (data) {
                    elemButtonSubmit.attr('disabled', false);
                    initCitySelect(previewContainer, data);
                    callback();
                });
            } else {
                initCitySelect(previewContainer);
                callback();
            }
            cityAppsChanged();
        }

        function goToBudgetProduct() {
            self.keepState = true;
            self.goToShop();
        }

        function showBudgetBalanceWarning() {
            var html = $.tmpl(templates.budget_balance_warning, {
                warning: CommonTranslations.budget_balance_warning,
            });

            var modal = sln.createModal(html);
            $('button[action=submit]', modal).click(function () {
                modal.modal('hide');
                goToBudgetProduct();
            });
        }

        function editCityApps() {
            if (self.citySelect) {
                self.citySelect.show();
            }
        }

        function checkRegionalNewsBudget(callback) {
            var appIds = getNewsFormData().app_ids;
            if (appIds.length === 1 && appIds[0] === ACTIVE_APPS[0]) {
                // only the default app, no budget is needed
                return callback();
            }

            if (self.freeRegionalNews()) {
                callback();
            } else {
                modules.billing.loadBudget(function (budget) {
                    if (budget.balance <= 0) {
                        showBudgetBalanceWarning();
                    } else {
                        callback();
                    }
                });
            }
        }

        function scheduleChanged() {
            var checked = elemCheckboxSchedule.prop('checked');
            elemInputScheduleDate.prop('disabled', !checked);
            elemInputScheduleTime.prop('disabled', !checked);
        }

        function previousStep() {
            if (elemButtonPrevious.attr('disabled')) {
                return;
            }
            var data = getNewsFormData();
            currentStep--;
            for (var i = currentStep; currentStep >= 0; i--) {
                if (!self.steps[i].type || self.steps[i].type === data.type) {
                    currentStep = i;
                    break;
                }
            }
            var step = self.steps[currentStep];
            if (step.tab === 1) {
                // When going back, ensure we save the image to avoid errors.
                resizeImage();
            }
            stepChanged(data);
        }

        function validateScheduledAt(data) {
            var error = '';
            if (data.scheduled_at && !itemIsPublished) {
                var now = new Date();
                if (data.scheduled_at <= (now.getTime() / 1000)) {
                    error = T('date_must_be_in_future');
                } else {
                    now.setDate(now.getDate() + 30);
                    if (data.scheduled_at > now.getTime() / 1000) {
                        error = T('broadcast-schedule-too-far-in-future');
                    }
                }
            }
            elemScheduledAtError.html(error);
            return !error;
        }

        function autoRequireActionButtonRoles() {
            var tag = elemSelectButton.val();
            var menuItem = self.serviceMenu.items.filter(function (item) {
                return item.tag === tag;
            })[0];

            if (!menuItem) {
                return;
            }

            $.each(menuItem.roles, function () {
                elemCheckboxesRoles.parent().find('input[type=checkbox][value=' + this + ']').prop('required', true);
            });
        }

        function nextStep() {
            if (elemButtonNext.attr('disabled')) {
                return;
            }
            var data = getNewsFormData();
            // Validate the current step before going to the next.
            if (!elemForm.valid()) {
                return;
            }

            var step = self.steps[currentStep];
            if (step.tab === 0) {
                // do not show post to social media if news type is coupon
                var elemPostToSocialMedia = self.$('#post_to_social_media');
                if (data.type === NEWS_TYPE_QR) {
                    elemCheckPostToFacebook.attr('checked', false);
                    elemCheckPostToTwitter.attr('checked', false);
                    elemPostToSocialMedia.hide();
                } else {
                    elemPostToSocialMedia.show();
                }
            }
            // Image step
            if (step.tab === 2) {
                resizeImage();
            }

            // check if the attachment is provided
            // the attachment url is hidden
            if (step.tab === 4) {
                elemCheckboxesRoles.prop('required', false);

                if (data.action_button) {
                    if (data.action_button.id === 'attachment') {
                        var attachmentUrl = self.$('#news_action_attachment_value').val().trim();
                        if (attachmentUrl === '') {
                            sln.alert(T('please_add_attachment'), null, CommonTranslations.ERROR);
                            return;
                        }
                    }

                    if (data.action_button.action.startsWith('smi')) {
                        autoRequireActionButtonRoles();
                    }
                }
            }
            if (step.tab === 5) {
                // schedule step
                var valid = validateScheduledAt(data);
                if (!valid) {
                    return;
                }
            }
            currentStep++;
            for (var i = currentStep; currentStep < self.steps.length; i++) {
                if (!self.steps[i].type || self.steps[i].type === data.type) {
                    currentStep = i;
                    break;
                }
            }
            stepChanged(data);
        }

        function stepChanged(data) {
            var step = self.steps[currentStep];

            if (step.tab === 0 && (MODULES.indexOf('loyalty') === -1 || OCA_LOYALTY_LIMITTED)) {
                nextStep();
                return;
            }

            var LAST_STEP = self.steps.length - 1;
            var isLastStep = currentStep === LAST_STEP;
            if (LAST_STEP - 1 === currentStep) {
                paidContentChanged();
            } else {
                elemButtonSubmit.hide();
                elemButtonNext.toggle(!isLastStep);
            }

            if (isLastStep) {
                shouldPay(function (pay) {
                    if (pay) {
                        elemNewsFormContainer.removeClass('span6').addClass('span12');
                        showNewsOrderPage(data);
                    } else {
                        elemNewsFormContainer.removeClass('span12').addClass('span6');
                    }
                });
            } else {
                elemNewsFormContainer.removeClass('span12').addClass('span6');
            }
            if (step.tab === 0) {
                elemButtonPrevious.attr('disabled', true);
            } else if (step.tab === 1 && MODULES.includes('joyn')) {
                elemButtonPrevious.attr('disabled', true);
            } else {
                elemButtonPrevious.attr('disabled', false).toggle(!isLastStep);
            }
            self.$('.tab-pane').removeClass('active');
            self.$('#tab' + step.tab).addClass('active');
            elemStepTitle.text(step.text);
            elemStepDescription.html(step.description);
            elemNewsPreview.toggle(!isLastStep);
            elemButtonSubmit.text(geSubmitButtonText(data));
            renderPreview();

            // target audience step
            if (step.tab == 6) {
                self.showBudget();
            }
        }

        function geSubmitButtonText(data) {
            var key;
            if (originalNewsItem) {
                key = 'Save';
            } else if (data.scheduled_at) {
                key = 'schedule';
            } else {
                key = 'publish';
            }
            return T(key);
        }

        function doRenderPreview() {
            Requests.getSettings().then(r);

            function r(settings) {
                var newsItem = getNewsFormData();
                var imageUrl = elemImagePreview.attr('src') || '';
                if (imageUrl.indexOf('http') === 0) {
                    newsItem.media = originalNewsItem.media;
                }
                newsItem.title = newsItem.title || T('title');
                var totalReach = self.getCityAppTotalReach(newsItem.app_ids);
                var html = $.tmpl(templates['broadcast/broadcast_news_preview'], {
                    defaultButtons: self.defaultButtons,
                    newsItem: newsItem,
                    htmlize: sln.htmlize,
                    settings: settings,
                    reach: totalReach,
                    currentDatetime: sln.formatDate(new Date().getTime() / 1000),
                    messageHtml: messageEditor.markdown(newsItem.message),
                });
                elemNewsPreview.html(html);
                $(elemNewsPreview).find('a').attr('target', '_blank');

                var elemShowMore = self.$('.news_read_more_text'),
                    elemNewsContent = self.$('.news_content');
                var hasMore = elemNewsContent.prop('scrollHeight') > 125;
                var moreOrLess = hasMore;

                function showMoreOrLess(more) {
                    elemShowMore.find('.read_more_text').toggle(!more);
                    elemShowMore.find('.read_less_text').toggle(more);
                    if (!hasMore) {
                        elemShowMore.hide();
                    } else {
                        if (more) {
                            elemShowMore.slideDown();
                        }
                    }
                    if (hasMore) {
                        var height = more ? elemNewsContent.prop('scrollHeight') + 'px' : '100px';
                        elemNewsContent.animate({
                            'max-height': height
                        });
                    }
                }

                elemShowMore.toggle(hasMore);
                elemShowMore.find('.read_more_text').toggle(hasMore);
                elemShowMore.find('.read_less_text').toggle(!hasMore);

                self.$('.read_more_trigger').click(function () {
                    showMoreOrLess(moreOrLess);
                    moreOrLess = !moreOrLess;
                });
            }
        }
    },

};
