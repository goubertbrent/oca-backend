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

function RequestsService() {
    this._requestCache = {};
}

RequestsService.prototype = {

    request: function (url, method, data, options) {
        if (!options) {
            options = {};
        }
        if (options.showError === undefined) {
            options.showError = true;
        }
        return new Promise(function (resolve, reject) {
            sln.call({
                url: url,
                type: method,
                data: data,
                success: function (data) {
                    resolve(data);
                },
                error: function () {
                    if (options.showError) {
                        sln.showAjaxError();
                    }
                    reject();
                }
            });
        });
    },
    /**
     * Do a request and cache the result.
     * If the function is called again with the same url, the previous result will be returned.
     * @param url{string}
     * @param options{{cached: boolean, showError: boolean, updatesCache: boolean}}
     * @return {Promise}
     */
    get: function (url, options) {
        if (!options) {
            options = {};
        }
        if (options.cached === undefined) {
            options.cached = true;
        }
        if (!this._requestCache[url] || !options.cached) {
            this._requestCache[url] = this.request(url, 'get', null, options);
        }
        return this._requestCache[url];
    },
    withCacheUpdate: function(url, method, data, options) {
        var request = this.request(url, method, data, options);

        // Update cache if updatesCache option is set, get and `method` must use the same url.
        if (options && options.updatesCache) {
            this._requestCache[url] = request;
        }
        return request;
    },
    clearCache: function(url) {
        delete this._requestCache[url];
    },
    post: function (url, data, options) {
        return this.withCacheUpdate(url, 'post', data, options);
    },
    put: function (url, data, options) {
        return this.withCacheUpdate(url, 'put', data, options);
    },
    delete: function(url, data, options) {
        return this.withCacheUpdate(url, 'delete', data, options);
    },
    getMenu: function (options) {
        return this.get('/common/menu/load', options);
    },
    getServiceMenu: function (options) {
        return this.get('/common/get_menu', options);
    },
    getBroadcastOptions: function (options) {
        return this.get('/common/broadcast/options', options);
    },
    getSandwichSettings: function (options) {
        return this.get('/common/sandwich/settings/load', options);
    },
    getAppStatistics: function (options) {
        return this.get('/common/statistics/apps', options);
    },
    getBudget: function (options) {
        return this.get('/common/billing/budget', options);
    },
    getAppSettings: function (options) {
        return this.get('/common/settings/app', options);
    },
    saveAppSettings: function (data, options) {
        options = options || {};
        options.updatesCache = true;
        return this.post('/common/settings/app', data, options);
    },
    getOrderSettings: function(options){
        return this.get('/common/order/settings', options);
    },
    saveOrderSettings: function(data, options){
        options = options || {};
        options.updatesCache = true;
        return this.post('/common/order/settings', data, options);
    },
    getPaymentSettings: function (options) {
        return this.get('/common/payments/settings', options);
    },
    savePaymentSettings: function(data, options){
        options = options || {};
        options.updatesCache = true;
        return this.post('/common/payments/settings', data, options);
    },
    getPaymentProviders: function (options) {
        return this.get('/common/payments/providers', options);
    },
    savePaymentProvider: function(providerId, data, options){
        return this.put('/common/payments/providers/' + providerId, data, options);
    },
    getSettings: function (options) {
        return this.get('/common/settings', options);
    },
    saveSettings: function(data, options){
        options = options || {};
        options.updatesCache = true;
        return this.put('/common/settings', data, options);
    },
    getAppTexts: function(options) {
        return this.get('/common/settings/app_texts', options);
    },
    updateAppText: function(data, options) {
        options = options || {};
        options.updatesCache = true;
        return this.post('/common/settings/app_texts', data, options);
    },
    removeAppText: function(data, options) {
        options = options || {};
        options.updatesCache = true;
        return this.delete('/common/settings/app_texts', data, options);
    },
};

var Requests = new RequestsService();
