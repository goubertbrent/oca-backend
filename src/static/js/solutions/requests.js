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
    post: function (url, data, options) {
        var request = this.request(url, 'post', data, options);
        // Update cache if updatesCache option is set, get and post must use the same url.
        if (options && options.updatesCache) {
            this._requestCache[url] = request;
        }
        return request;
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
    }
};

var Requests = new RequestsService();