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

var AnswerType = {
    multiple_choice: 1,
    checkboxes: 2,
}


var PollsIndicator = new LoadingIndicator($('#polls_loading_indicator'));

function PollsList(container) {
    'use strict';

    ScrollableList.call(this, container, {
        itemClass: 'poll',
    });
}

PollsList.prototype = Object.create(ScrollableList.prototype);
PollsList.prototype.constructor = PollsList;
PollsList.prototype.load = function() {
    this.isLoading = true;
    PollsIndicator.show();
    PollsRequests.getPolls(this.cursor).then(function(data) {
        this.onLoaded(data);
        PollsIndicator.hide();
    }.bind(this));
};
PollsList.prototype.render = function(polls) {
    var self = this;
    $.each(polls, function(i, poll) {
        var row = $.tmpl(templates['polls/poll_row'], {
            t: CommonTranslations,
            poll: poll
        });
        self.container.append(row);
    });
};
PollsList.prototype.reload = function() {
    this.reset();
    PollsRequests.clearGetPolls();
    this.container.empty();
    this.load();
};

$(function() {
    'use strict';
    var list;
    var currentPoll = {
        status: PollStatus.pending
    };

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
                renderPollsForm(parseInt(urlHash[2]));
                break;
            case 'result':
                renderResultsForPoll(parseInt(urlHash[2]));
                break;
            default:
                showList();
                break;

        }
    }

    function initPollsList() {
        var container = $('.polls-list');
        list = new PollsList(container);
        list.load();
    }


    function showList() {
        $('.polls-container').hide();
        $('#polls-list-container').show();
    }

    function populateFormData() {
        currentPoll.name = $('#poll-name').val().trim();
        if ($('#poll-end-date input').val().trim()) {
            currentPoll.ends_on = $('#poll-end-date').data('datepicker').date.valueOf() / 1000;
        }
    }

    function updateSuccess() {
        PollsIndicator.hide();
        window.location.href = '#/polls';
        list.reload();
    }

    function renderQuestionList() {
        return lockIfReadonly(
            $.tmpl(templates['polls/question_list'], {
                questions: currentPoll.questions,
                t: CommonTranslations,
            })
        );
    }

    function populateQuestionList() {
        $('#poll-form-container').find('#question-list').html(renderQuestionList());
    }

    function lockIfReadonly(container) {
        if (currentPoll.status !== PollStatus.pending) {
            container.find('button').prop('disabled', true);
            container.find('fieldset').prop('disabled', true);
        }
        return container;
    }

    function renderPollsForm(pollId) {
        var formContainer = $('#poll-form-container');
        $('.polls-container').hide();
        formContainer.show()

        function render() {
            var html = lockIfReadonly($.tmpl(templates['polls/poll_form'], {
                t: CommonTranslations,
                edit: !!pollId,
                readonly: currentPoll.status !== PollStatus.pending,
                poll: currentPoll,
                dateFormat: sln.getLocalDateFormat(),
            }));
            formContainer.html(html);
            var datePicker = $('.date').datepicker({
                format : sln.getLocalDateFormat()
            })
            if (currentPoll.ends_on) {
                datePicker.datepicker('setValue', new Date(currentPoll.ends_on * 1000));
            }
            populateQuestionList();
        }

        if (pollId) {
            PollsIndicator.show();
            PollsRequests.getPoll(pollId).then(function(poll) {
                PollsIndicator.hide();
                currentPoll = poll;
                render();
            });
        } else {
            currentPoll = {
                id: null,
                name: '',
                questions: [],
                status: PollStatus.pending,
            };
            render();
        }
    }

    function savePoll() {
        populateFormData();
        if (!currentPoll.name) {
            sln.alert(CommonTranslations.NAME_REQUIRED, null, CommonTranslations.ERROR);
            return;
        }
        if (!currentPoll.ends_on) {
            sln.alert(CommonTranslations.poll_has_no_end_date, null, CommonTranslations.ERROR);
            return;
        }
        if (!currentPoll.questions.length) {
            sln.alert(CommonTranslations.poll_has_no_questions, null, CommonTranslations.ERROR);
            return;
        }

        if (currentPoll.id) {
            PollsRequests.updatePoll(currentPoll).then(updateSuccess);
        } else {
            PollsRequests.createPoll(currentPoll).then(updateSuccess);
        }
    }

    function pollActionSuccess() {
        PollsIndicator.hide();
        list.reload();
    }

    function startPoll(pollId) {
        PollsRequests.startPoll(pollId).then(pollActionSuccess);
    }

    function stopPoll(pollId) {
        PollsRequests.stopPoll(pollId).then(pollActionSuccess);
    }

    function removePoll(pollId) {
        PollsRequests.removePoll(pollId).then(pollActionSuccess);
    }

    function confirmPollAction(message, callback) {
        var pollId = parseInt($(this).parent().attr('poll_id'));
        sln.confirm(message, function() {
            PollsIndicator.show();
            callback(pollId);
        });
    }
    function confirmStartPoll() {
        confirmPollAction.bind(this)(CommonTranslations.poll_start_are_you_sure, startPoll);
    }

    function confirmStopPoll() {
        confirmPollAction.bind(this)(CommonTranslations.poll_stop_are_you_sure, stopPoll);
    }

    function confirmRemovePoll() {
        confirmPollAction.bind(this)(CommonTranslations.poll_remove_are_you_sure, removePoll);
    }

    function addQuestion() {
        renderQuestionModal({
            text: '',
            answer_type: AnswerType.multiple_choice,
            optional: true,
            choices: [],
        }, function(question) {
            currentPoll.questions.push(question);
            populateQuestionList();
        });
    }

    function editQuestion() {
        var questionId = parseInt($(this).attr('question_id'));
        renderQuestionModal(currentPoll.questions[questionId], function(question) {
            currentPoll.questions[questionId] = question;
            populateQuestionList();
        });
    }

    function swapQuestions(aIndex, bIndex) {
        var aQuestion = currentPoll.questions[aIndex];
        currentPoll.questions[aIndex] = currentPoll.questions[bIndex];
        currentPoll.questions[bIndex] = aQuestion;
        populateQuestionList();
    }

    function moveQuestionUp() {
        var questionId = parseInt($(this).attr('question_id'));
        swapQuestions(questionId - 1, questionId);
    }

    function moveQuestionDown() {
        var questionId = parseInt($(this).attr('question_id'));
        swapQuestions(questionId + 1, questionId);
    }

    function removeQuestion() {
        var questionId = parseInt($(this).attr('question_id'));
        var question = currentPoll.questions[questionId];
        sln.confirm(CommonTranslations.confirm_delete_x.replace('%(x)s', question.text), function() {
            currentPoll.questions.splice(questionId, 1);
            populateQuestionList();
        });
    }

    function hasChoices(type) {
        return type === AnswerType.multiple_choice || type === AnswerType.checkboxes;
    }

    function renderQuestionModal(question, callback) {
        var html = lockIfReadonly($.tmpl(templates['polls/question_form'], {
            t: CommonTranslations,
            question: question,
            readonly: currentPoll.status !== PollStatus.pending,
            AnswerType: AnswerType,
        }));

        var modal = sln.createModal(html);
        var choicesContainer = $('#question-choices', modal);
        var choiceInput = $('#new-choice-text', modal);
        var addChoiceButton = $('#add-choice', modal);
        renderChoices();

        function getQuestionData() {
            var choices = $('.question-choice', modal).map(function(i, el) {
                return {
                    text: $(el).attr('choice'),
                };
            }).get();

            return {
                text: $('#question-text', modal).val().trim(),
                answer_type: parseInt($('#question-type', modal).val()),
                optional: $('#question-optional').is(':checked'),
                choices: choices,
            }
        }

        function renderChoice(type, choice) {
            return lockIfReadonly($.tmpl(templates['polls/question_choice'], {
                choice: choice,
                type: type,
                AnswerType: AnswerType,
            }));
        }

        function renderChoices(answerType, choices) {
            answerType = answerType || question.answer_type;
            choices = choices || question.choices;
            var showChoices = hasChoices(answerType);
            $('#question-choices-group', modal).toggle(showChoices);

            if (showChoices) {
                choicesContainer.empty();
                $.each(choices, function(i, choice) {
                    choicesContainer.append(renderChoice(answerType, choice.text));
                });
            }
        }

        function saveQuestion() {
            var question = getQuestionData();
            if (!question.text) {
                sln.alert(CommonTranslations.text_is_required, null, CommonTranslations.ERROR);
                return;
            }
            if (hasChoices(question.answer_type) && question.choices.length < 2) {
                sln.alert(CommonTranslations.add_2_choices_at_least, null, CommonTranslations.ERROR);
                return;
            }
            callback(question);
            modal.modal('hide');
        }

        function answerTypeChanged() {
            var question = getQuestionData();
            renderChoices(question.answer_type, question.choices);
        }

        function addChoice() {
            var question = getQuestionData();
            var value = choiceInput.val().trim();
            if (value) {
                var choice = renderChoice(question.answer_type, choiceInput.val());
                choicesContainer.append(choice);
                choiceInput.val('');
            }
        }

        function removeChoice() {
            var choice = $(this).attr('choice');
            $(`.question-choice[choice="${choice}"]`).remove();
        }

        function choiceInputChanged() {
            addChoiceButton.prop('disabled', !choiceInput.val().trim());
        }

        $('button[action=submit]', modal).click(saveQuestion);
        $('#question-type', modal).change(answerTypeChanged);
        choiceInput.keyup(choiceInputChanged);
        addChoiceButton.click(addChoice);
        $(modal).on('click', '.remove-choice', removeChoice);
    }

    function renderResultsForPoll(pollId) {
        var resultsContainer = $('#poll-results-container');
        $('.polls-container').hide();
        resultsContainer.show();

        function drawChart(containerId, title, chartData) {
            var wrapper = new google.visualization.ChartWrapper({
                chartType: 'BarChart',
                dataTable: google.visualization.arrayToDataTable(chartData),
                options: {
                    title: title,
                    legend: {
                        position: 'none'
                    },
                    width: 600,
                    animation: {duration: 1000, easing: 'out', startup: true}
                },
                containerId: containerId,
            });
            wrapper.draw();
        }

        function render(questions) {
            var html = $.tmpl(templates['polls/poll_result'], {
                t: CommonTranslations,
            });
            resultsContainer.html(html);
            var countsContainer = $('#poll-counts', resultsContainer);

            countsContainer.show().empty();
            $.each(questions, function(questionId, question) {
                var container = $.tmpl(templates['polls/poll_count_graph'], {
                        pollId: pollId,
                        questionId: questionId,
                });
                countsContainer.append(container);
                var containerId = container.find('.poll-graph').attr('id');

                var chartData = [['', '', { role: 'annotation' }]];
                $.each(question.choices, function(j, choice) {
                    chartData.push([choice.text, choice.count, choice.count]);
                });

                drawChart(containerId, question.text, chartData);
            });

            PollsIndicator.hide();
        }

        PollsIndicator.show();
        PollsRequests.getPollResult(pollId).then(function(questions) {
            render(questions);
        });
    }

    $(document).on('click', '#poll-submit', savePoll);
    $(document).on('click', '.run-poll', confirmStartPoll);
    $(document).on('click', '.stop-poll', confirmStopPoll);
    $(document).on('click', '.remove-poll', confirmRemovePoll);
    $(document).on('click', '#add-question', addQuestion);
    $(document).on('click', '.edit-question', editQuestion);
    $(document).on('click', '.up-question', moveQuestionUp);
    $(document).on('click', '.down-question', moveQuestionDown);
    $(document).on('click', '.remove-question', removeQuestion);
});
