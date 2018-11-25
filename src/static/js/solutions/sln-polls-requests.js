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
    return result.catch(this.showError.bind(this));
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
PollsRequestsService.prototype.getPolls = function(status, cursor, limit) {
    var params = {status: status};
    if (cursor) {
        params.cursor = cursor;
    }
    if (limit) {
        params.limit = limit;
    }
    return this.get(`${this.baseUrl}?${$.param(params)}`);
};
PollsRequestsService.prototype.clearGetPolls = function(status) {
    var self = this;
    $.each(self._requestCache, function(url, _) {
        if (url.startsWith(`${self.baseUrl}?status=${status}`)) {
            self.clearCache(url);
        }
    });
};
PollsRequestsService.prototype.createPoll = function(poll) {
    return this.post(this.baseUrl, poll);
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

PollsRequests = new PollsRequestsService();
