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

function PollsList(status, container) {
    this.status = status;
    this.container = container;

    this.polls = [];
    this.cursor = null;
    this.has_more = true;
}

PollsList.prototype = {
    loadPolls: function() {
        PollsRequests.getPolls(this.status, this.cursor).then(function(data) {
            this.polls = this.polls.concat(data.results);
            this.cursor = data.cursor;
            this.has_more = data.more;
            this.renderPolls(data.results);
        }.bind(this));
    },

    renderPolls: function(polls) {
        var self = this;
        $.each(polls, function(i, poll) {
            var row = $.tmpl(templates['polls/poll_row'], {
                poll: poll
            });
            self.container.append(row);
        });
    },

    validateLoadMore: function() {

    },
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
            var status = PollStatus[name];
            var list = new PollsList(status, $(container));
            lists[status] = list;
            list.loadPolls();
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
