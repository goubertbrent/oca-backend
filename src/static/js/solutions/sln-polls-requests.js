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

var PollStatus = {
    pending: 1,
    running: 2,
    completed: 3,
};

function PollsRequestsService() {
    RequestsService.call(this);
    this.baseUrl = '/common/polls';
}

PollsRequestsService.prototype = Object.create(RequestsService.prototype)
PollsRequestsService.prototype.constructor = PollsRequestsService;

PollsRequestsService.prototype.getDefaultOptions = function(options) {
    // prefered options here
    options = options || {};
    if (!options.hasOwnProperty('cached')) {
        options.cached = true;
    }
    if (!options.hasOwnProperty('updatesCache')) {
        options.updatesCache = true;
    }
    if (!options.hasOwnProperty('showError')) {
        options.showError = false;
    }
    return options;
};
PollsRequestsService.prototype.request = function(url, method, data, options) {
    options = this.getDefaultOptions(options);
    var result = RequestsService.prototype.request.call(this, url, method, data, options);
    var self = this;
    return result.catch(function(error) {
        self.clearCache(url);
        self.showError(error);
    });
};
PollsRequestsService.prototype.withCacheUpdate = function(url, method, data, options) {
    options = this.getDefaultOptions(options);
    return RequestsService.prototype.withCacheUpdate.call(this, url, method, data, options);
};
PollsRequestsService.prototype.showError = function(error) {
    var errorMsg;
    if (error.status === 404 || error.status === 400 && error.responseJSON) {
        errorMsg = error.responseJSON.error;
        sln.alert(CommonTranslations[errorMsg], null, CommonTranslations.ERROR);
    } else {
        errorMsg = 'unknown error'
        sln.showAjaxError();
    }
    throw new Error('polls requests error, ' + errorMsg);
};
PollsRequestsService.prototype.getPolls = function(cursor, limit) {
    var url = this.baseUrl;
    var params = {};
    if (cursor) {
        params.cursor = cursor;
    }
    if (limit) {
        params.limit = limit;
    }
    if (Object.keys(params).length) {
        url += `?${$.param(params)}`;
    }
    return this.get(url);
};
PollsRequestsService.prototype.clearGetPolls = function() {
    var self = this;
    $.each(self._requestCache, function(url, _) {
        if (url.startsWith(`${self.baseUrl}?`) || url === self.baseUrl) {
            self.clearCache(url);
        }
    });
};
PollsRequestsService.prototype.createPoll = function(poll) {
    poll.id = null;
    return this.post(this.baseUrl, poll, {
        updatesCache: false,
    });
};
PollsRequestsService.prototype.getPoll = function(pollId) {
    return this.get(`${this.baseUrl}/${pollId}`);
};
PollsRequestsService.prototype.updatePoll = function(poll) {
    return this.post(`${this.baseUrl}/${poll.id}`, poll);
};
PollsRequestsService.prototype.startPoll = function(pollId) {
    return this.put(`${this.baseUrl}/${pollId}`, {status: PollStatus.running});
};
PollsRequestsService.prototype.stopPoll = function(pollId) {
    return this.put(`${this.baseUrl}/${pollId}`, {status: PollStatus.completed});
};
PollsRequestsService.prototype.removePoll = function(pollId) {
    return this.delete(`${this.baseUrl}/${pollId}`);
};
PollsRequestsService.prototype.getPollResult = function(pollId) {
    return this.get(`${this.baseUrl}/result/${pollId}`);
}
PollsRequests = new PollsRequestsService();
