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
