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
    running: 2,
    completed: 3,
};

var AnswerType = {
    multiple_choice: 1,
    checkboxes: 2,
}


$(function () {
    'use strict';

    var API_METHOD_LOAD = 'solutions.polls.load';
    var API_METHOD_SUBMIT = 'solutions.polls.submit';
    var methodCallbacks = {};
    var polls = [];
    var currentPoll = {};
    var currentAnswer = {};

    function init() {
        if (typeof rogerthat === 'undefined') {
            document.body.innerHTML = EventsTranslations.ROGERTHAT_FUNCTION_UNSUPPORTED_UPDATE;
            return;
        }

        rogerthat.callbacks.ready(onRogerthatReady);
    }

    init();

    function backPressed() {
        console.log("BACK pressed");
        $.mobile.navigate('#polls');
        return true; // we handled the back press
    }

    function onRogerthatReady() {
        console.log("onRogerthatReady()");

        rogerthat.callbacks.backPressed(backPressed);
        rogerthat.api.callbacks.resultReceived(onReceivedApiResult);

        loadPolls();
    }

    /*
        element id helper for templates
    */
    function ID() {
        var args = ['poll'];
        args = args.concat(Array.prototype.slice.call(arguments));
        return args.join('-');
    }

    /*
        render a template with default params
    */
    function render(name, params) {
        if (!templates[name]) {
            throw Error('template ' + name + ' is not found');
        }

        params = params || {};
        params.t = PollsTranslations;
        params.ID = ID;

        return $.tmpl(templates[name], params);
    }

    function renderPollPage(poll) {
        var page = render('poll_page', {
            poll: poll,
            PollStatus: PollStatus,
        });

        if (poll.status == PollStatus.running) {
            var questions = render('poll_questions', {
                poll: poll,
                AnswerType: AnswerType,
            });
            $.mobile.pageContainer.append(questions);
        }

        $.mobile.pageContainer.append(page);
    }

    function renderPollList(polls) {
        if (!polls || !polls.length) {
            $('#polls-empty').show();
            return;
        }

        $.each(polls, function(i, poll) {
            var item = render('poll_item', {
                poll: poll,
            });

            renderPollPage(poll);
            $('#polls-list').append(item);
        });
    }

    function showLoading(message) {
        $.mobile.loading('show', {
            text: message,
            textVisible: true,
            theme: 'a',
            html: ''
        });
    }

    function showDialog(title, message) {
        var dialog = render('poll_popup', {
            title: title,
            message: message,
        });

        $('#popupDialog').remove();
        $.mobile.pageContainer.append(dialog);
        $('#popupDialog').popup().popup('open');
    }

    function loadPolls() {
        showLoading(PollsTranslations.loading_polls);
        rogerthat.api.call(API_METHOD_LOAD, '', '');
    }

    function pollsLoaded(result) {
        polls = result;
        renderPollList(result);
    }
    methodCallbacks[API_METHOD_LOAD] = pollsLoaded;

    function pollSubmitted(result) {
        $('#' + ID(result.id)).remove();
        renderPollPage(result);
        $.mobile.navigate('#polls');
    }
    methodCallbacks[API_METHOD_SUBMIT] = pollSubmitted;

    function onReceivedApiResult(method, result, error, tag) {
        console.log("onReceivedApiResult");
        console.log("method: " + method);
        console.log("result: " + result);
        console.log("error: " + error);
        console.log("tag: " + tag);

        var result = JSON.parse(result);
        $.mobile.loading('hide');

        if (error) {
            showDialog('Error', error);
            return;
        }

        if (methodCallbacks[method]) {
            methodCallbacks[method](result);
        }
    }

    function getPoll(pollId) {
        return polls.filter(function(poll) {
            return poll.id === pollId;
        })[0];
    }

    function open() {
        var pollId = parseInt($(this).attr('href').split('-')[1]);
        currentPoll = getPoll(pollId);
        currentAnswer = {};
    }

    function submitAnswer(answer) {
        answer.poll_id = currentPoll.id;
        rogerthat.api.call(API_METHOD_SUBMIT, JSON.stringify(answer), '');
        showLoading(PollsTranslations.submitting_answer);
    }

    function next() {
        var pollId = currentPoll.id;
        var questionId = parseInt($(this).attr('question_id'));
        var question = currentPoll.questions[questionId];
        var choices = [];

        $.each(question.choices, function(choiceId, choice) {
            var el = $('#' + ID(pollId, questionId, choiceId));
            if (el.is(':checked')) {
                choices.push({
                    question_id: questionId,
                    choice_id: choiceId
                });
            }
        });

        if (!choices.length && !question.optional) {
            showDialog(PollsTranslations.required, PollsTranslations.answer_is_required);
            return;
        }

        currentAnswer = currentAnswer || {};
        currentAnswer.choices = currentAnswer.choices || [];
        currentAnswer.choices = currentAnswer.choices.concat(choices);

        if (questionId === currentPoll.questions.length - 1) {
            $.mobile.navigate('#' + ID(pollId, 'result-notification'));
        } else {
            $.mobile.navigate('#' + ID(pollId, questionId + 1));
        }
    }

    function submit() {
        var pollId = currentPoll.id;
        $(this).prop('disabled', true);
        currentPoll.answered = true;
        currentAnswer.notify = $('#' + ID(pollId, 'notify-results-yes')).is(':checked');
        submitAnswer(currentAnswer);
    }

    $(document).on('click', '.poll-open', open);
    $(document).on('click', '.poll-submit', submit);
    $(document).on('click', '.question-next', next);
});