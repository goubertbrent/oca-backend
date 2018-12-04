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

var QuestionType = {
    multiple_choice: 1,
    checkboxes: 2,
    short_text: 3,
    long_text: 4
}


var PollsIndicator = new LoadingIndicator($('#polls_loading_indicator'));

function PollsList(status, container) {
    'use strict';

    ScrollableList.call(this, container, {
        itemClass: 'poll',
    });

    this.status = status;
}

PollsList.prototype = Object.create(ScrollableList.prototype);
PollsList.prototype.constructor = PollsList;
PollsList.prototype.load = function() {
    this.isLoading = true;
    PollsIndicator.show();
    PollsRequests.getPolls(this.status, this.cursor).then(function(data) {
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
    PollsRequests.clearGetPolls(this.status);
    this.container.empty();
    this.load();
};


function PollAnswerList(poll, container) {
    ScrollableList.call(this, container);

    this.poll = poll;
}

PollAnswerList.prototype = Object.create(ScrollableList.prototype);
PollAnswerList.prototype.constructor = PollAnswerList;
PollAnswerList.prototype.load = function() {
    this.isLoading = true;
    PollsIndicator.show();
    PollsRequests.getPollAnswers(this.poll.id, this.cursor).then(function(data) {
        this.onLoaded(data);
        PollsIndicator.hide();
    }.bind(this));
};
PollAnswerList.prototype.render = function(answers) {
    var self = this;
    var rows = $.tmpl(templates['polls/poll_answer_row'], {answers: answers})
    self.container.append(rows);
};
PollAnswerList.prototype.reload = function() {
    this.reset();
    this.container.empty();
    this.load();
};


$(function() {
    'use strict';
    var lists = {};
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
                showLists();
                break;

        }
    }

    function initPollsList() {
        $('.polls-list').each(function(i, container) {
            var name = $(this).attr('id').split('-')[0];
            var status = PollStatus[name];
            var list = new PollsList(status, $(container));
            lists[status] = list;
            list.load();
        });
    }


    function showLists() {
        $('.polls-container').hide();
        $('#polls-list-container').show();
    }

    function getCurrentList() {
        return lists[currentPoll.status];
    }

    function populateFormData() {
        currentPoll.name = $('#poll-name').val().trim();
        currentPoll.is_vote = $('#poll-is-vote').is(':checked');
    }

    function updateSuccess() {
        PollsIndicator.hide();
        window.location.href = '#/polls';
        getCurrentList().reload();
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
            }));
            formContainer.html(html);
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
                is_vote: false,
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

    function startPoll() {
        var pollId = parseInt($(this).parent().attr('poll_id'));
        PollsRequests.startPoll(pollId).then(function(poll) {
            lists[PollStatus.pending].reload();
            lists[poll.status].reload();
        });
    }

    function stopPoll() {
        var pollId = parseInt($(this).parent().attr('poll_id'));
        PollsRequests.stopPoll(pollId).then(function(poll) {
            lists[PollStatus.running].reload();
            lists[poll.status].reload();
        });
    }

    function removePoll() {
        var pollId = parseInt($(this).parent().attr('poll_id'));
        var status = parseInt($(this).parent().attr('poll_status'));
        PollsRequests.removePoll(pollId).then(function() {
            lists[status].reload();
        });
    }

    function confirmStartPoll() {
        sln.confirm(CommonTranslations.poll_start_are_you_sure, startPoll.bind(this));
    }

    function confirmStopPoll() {
        sln.confirm(CommonTranslations.poll_stop_are_you_sure, stopPoll.bind(this));
    }

    function confirmRemovePoll() {
        sln.confirm(CommonTranslations.poll_remove_are_you_sure, removePoll.bind(this));
    }

    function addQuestion() {
        renderQuestionModal({
            text: '',
            type: QuestionType.multiple_choice,
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
        return type === QuestionType.multiple_choice || type === QuestionType.checkboxes;
    }

    function renderQuestionModal(question, callback) {
        var html = lockIfReadonly($.tmpl(templates['polls/question_form'], {
            t: CommonTranslations,
            question: question,
            readonly: currentPoll.status !== PollStatus.pending,
        }));

        var modal = sln.createModal(html);
        var choicesContainer = $('#question-choices', modal);
        var choiceInput = $('#new-choice-text', modal);
        var addChoiceButton = $('#add-choice', modal);
        renderChoices();

        function getQuestionData() {
            var choices = $('.question-choice', modal).map(function(i, el) {
                return $(el).attr('choice');
            }).get();

            return {
                text: $('#question-text', modal).val().trim(),
                type: parseInt($('#question-type', modal).val()),
                required: $('#question-required').is(':checked'),
                choices: choices,
            }
        }

        function renderChoice(type, choice) {
            return lockIfReadonly($.tmpl(templates['polls/question_choice'], {
                choice: choice,
                type: type,
                QuestionType: QuestionType,
            }));
        }

        function renderChoices(questionType, choices) {
            questionType = questionType || question.type;
            choices = choices || question.choices;
            var showChoices = hasChoices(questionType);
            $('#question-choices-group', modal).toggle(showChoices);

            if (showChoices) {
                choicesContainer.empty();
                $.each(choices, function(i, choice) {
                    choicesContainer.append(renderChoice(questionType, choice));
                });
            }
        }

        function saveQuestion() {
            var question = getQuestionData();
            if (!question.text) {
                sln.alert(CommonTranslations.text_is_required, null, CommonTranslations.ERROR);
                return;
            }
            if (hasChoices(question.type) && question.choices.length < 2) {
                sln.alert(CommonTranslations.add_2_choices_at_least, null, CommonTranslations.ERROR);
                return;
            }
            callback(question);
            modal.modal('hide');
        }

        function questionTypeChanged() {
            var question = getQuestionData();
            renderChoices(question.type, question.choices);
        }

        function addChoice() {
            var question = getQuestionData();
            var value = choiceInput.val().trim();
            if (value) {
                var choice = renderChoice(question.type, choiceInput.val());
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
        $('#question-type', modal).change(questionTypeChanged);
        choiceInput.keyup(choiceInputChanged);
        addChoiceButton.click(addChoice);
        $(modal).on('click', '.remove-choice', removeChoice);
    }

    function renderResultsForPoll(pollId) {
        var resultsContainer = $('#poll-results-container');
        $('.polls-container').hide();
        resultsContainer.show();

        function render(poll) {
            var html = $.tmpl(templates['polls/poll_result'], {
                t: CommonTranslations,
                poll: poll,
            });
            resultsContainer.html(html);
            var answersContainer = $('#poll-answers', resultsContainer);
            var countsContainer = $('#poll-counts', resultsContainer);
            var showAnswersButton = $('#show-poll-answers', resultsContainer);
            var showCountsButton = $('#show-poll-counts', resultsContainer);
            var answerList;

            function showHideContainers(isCounts) {
                answersContainer.toggle(!isCounts);
                countsContainer.toggle(isCounts);
                showAnswersButton.toggleClass('active', !isCounts);
                showCountsButton.toggleClass('active', isCounts);
            }

            function renderPollAnswers() {
                showHideContainers(false);

                if (!answerList) {
                    var container = resultsContainer.find('#answers_container');
                    answerList = new PollAnswerList(poll, container, {
                        itemClass: 'poll-answer',
                    });
                    answerList.load();
                }
            }

            function renderPollCounts() {
                function drawChart(containerId, title, chartData) {
                    var maxValue = Math.max(chartData.map(function(data) {
                        return data[data.length - 1];
                    }));
                    var wrapper = new google.visualization.ChartWrapper({
                        chartType: 'BarChart',
                        dataTable: google.visualization.arrayToDataTable(chartData),
                        options: {
                            title: title,
                            legend: {
                                position: 'none'
                            },
                            width: 500,
                            animation: {duration: 1000, easing: 'out', startup: true}
                        },
                        containerId: containerId,
                    });
                    wrapper.draw();
                }

                showHideContainers(true);
                countsContainer.empty();
                PollsIndicator.show();
                PollsRequests.getPollCounts(poll.id).then(function(questionCounts) {
                    PollsIndicator.hide();
                    $.each(questionCounts, function(i, questionCount) {
                        var questionText = poll.questions[questionCount.question_id].text;
                        var container = $.tmpl(templates['polls/poll_count_graph'], {
                                poll: poll,
                                question_count: questionCount,
                        });
                        countsContainer.append(container);
                        var containerId = container.find('.poll-graph').attr('id');

                        var chartData = [['', '', { role: 'annotation' }]];
                        $.each(questionCount, function(j, choiceCounts) {
                            $.each(choiceCounts, function(k, choiceCount) {
                                chartData.push([choiceCount.choice, choiceCount.count, choiceCount.count]);
                            });
                        });

                        drawChart(containerId, questionText, chartData);
                    });
                });
            }

            showAnswersButton.click(renderPollAnswers);
            showCountsButton.click(renderPollCounts);

            if (poll.is_vote) {
                renderPollCounts();
            } else {
                renderPollAnswers();
            }
        }

        PollsIndicator.show();
        PollsRequests.getPoll(pollId).then(function(poll) {
            currentPoll = poll;
            PollsIndicator.hide();
            render(poll);
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
