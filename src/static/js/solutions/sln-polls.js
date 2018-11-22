function PollsList(status) {
    this.status = status;
    this.polls = [];
}

PollsList.prototype = {
    loadPolls: function() {

    },

    validateLoadMore: function() {

    },
};


var POLL_STATUS = {
    pending: 1,
    running: 2,
    previous: 3,
};

$(function() {
    'use strict';
    var lists = {};

    function init() {
        ROUTES.polls = router;
        initPollsList();
    }

    init();

    function router(urlHash) {
        var page = urlHash[1];

        switch(page) {
            case 'add':
                renderPollsForm();
                break;
            case 'edit':
                renderPollsForm();
                break;
            default:
                loadPolls();
                break;

        }
    }

    function initPollsList() {
        $('.polls-list').each(function(i, container) {
            var name = $(this).attr('id').split('-')[0];
            var status = POLL_STATUS[name];
            lists[status] = new PollsList(status, $(container));
        });
    }

    function renderPollsForm() {
        $('#polls-list-container').hide();
        $('#poll-form-container').show();

        var html = $.tmpl(templates['polls/poll_form'], {
            t: CommonTranslations,
        });

        $('#poll-form-container').html(html);
    }

    function loadPolls() {
        renderPollsList();
    }

    function renderPollsList() {
        $('#polls-list-container').show();
        $('#poll-form-container').hide();
    }

});
