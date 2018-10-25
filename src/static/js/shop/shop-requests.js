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
                error: function (error) {
                    if (options.showError) {
                        if (error.responseJSON && error.responseJSON.error) {
                            sln.alert(error.responseJSON.error);
                        } else {
                            sln.showAjaxError();
                        }
                    }
                    reject(error);
                }
            });
        });
    },
    /**
     * Do a request and cache the result.
     * If the function is called again with the same url, the previous result will be returned.
     * @param url{string}
     * @param options{{cached: boolean, showError: boolean}}
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
    /**
     * Do a request and possibly update the cached result
     * @param url{string}
     * @param data{object}
     * @param options{{cached: boolean, showError: boolean, updatesCache: boolean}}
     * @return {Promise}
     */
    post: function (url, data, options) {
        var request = this.request(url, 'post', data, options);
        // Update cache if updatesCache option is set, get and post must use the same url.
        if (options && options.updatesCache) {
            this._requestCache[url] = request;
        }
        return request;
    },
    /**
     * Do a request and possibly update the cached result
     * @param url{string}
     * @param data{object}
     * @param options{{cached: boolean, showError: boolean, updatesCache: boolean}}
     * @return {Promise}
     */
    put: function (url, data, options) {
        var request = this.request(url, 'put', data, options);
        // Update cache if updatesCache option is set, get and put must use the same url.
        if (options && options.updatesCache) {
            this._requestCache[url] = request;
        }
        return request;
    },
    delete: function (url, options) {
        return this.request(url, 'delete', options);
    },
    getContacts: function (customerId, options) {
        return this.get(`/internal/shop/rest/customers/${customerId}/contacts`, options);
    },
    addContact: function(customerId, contact, options){
        return this.post(`/internal/shop/rest/customers/${customerId}/contacts`, contact, options);
    },
    updateContact: function(customerId, contactId, contact, options){
        return this.put(`/internal/shop/rest/customers/${customerId}/contacts/${contactId}`, contact, options);
    },
    deleteContact: function (customerId, contactId, options) {
        return this.delete(`/internal/shop/rest/customers/${customerId}/contacts/${contactId}`, options);
    },
    getQuotations: function(customerId, options){
        return this.get(`/internal/shop/rest/customers/${customerId}/quotations`, options);
    },
    createQuotation: function(customerId, quotation, options){
        return this.post(`/internal/shop/rest/customers/${customerId}/quotations`, quotation, options);
    },
    getProducts: function(language, options){
        return this.get(`/internal/shop/rest/products?language=${language}`, options);
    }
};

var ShopRequests = new RequestsService();
