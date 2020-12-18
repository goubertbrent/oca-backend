/*
 * Copyright 2020 Green Valley Belgium NV
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
 * @@license_version:1.7@@
 */

$(function() {
    var questions = {};
    var myQuestions = [];

    var loadMyQuestionsRequestData = {count: 10, cursor: null};

    ROUTES['qanda'] = qandaRouter;
    var isInitialized = false;

    function qandaRouter() {
        if (!isInitialized) {
            isInitialized = true;
            loadMyQuestions(true);
        }
    }

    $("#qanda li a").click(function () {
        $("#qanda li").removeClass("active");
        var li = $(this).parent().addClass("active");
        $("#qanda section").hide();
        $("#qanda section#" + li.attr("section")).show();
    });

    $("#send_question").click(function() {
		var title = $("#qanda #title").val().trim();
		var question = $("#qanda #question").val().trim();
		var tags = [];
		$("#qanda #tags input:checked").each(function () {
			tags.push($(this).val());
		});

        var errorlist = [];
        if (!title) {
            errorlist.push("<li>" + CommonTranslations.TITLE_IS_REQUIRED + "</li>");
        }
        if (!question) {
            errorlist.push("<li>" + CommonTranslations.DESCRIPTION_IS_REQUIRED + "</li>");
        }

        if (errorlist.length > 0) {
            errorlist.splice(0, 0, "<ul>");
            errorlist.push("</ul>");
            sln.alert(errorlist.join(""), null, CommonTranslations.ERROR);
            return;
        }

        sln.showProcessing(CommonTranslations.SAVING_DOT_DOT_DOT);
		sln.call({
			url: '/common/qanda/ask',
			type: 'POST',
			data: {
				data: JSON.stringify({
					title: title,
					description: question,
					modules: tags
				})
			},
			success: function () {
				sln.hideProcessing();
				$("#qanda #title").val("");
				$("#qanda #question").val("");
				$("#qanda #tags input:checked").prop('checked', false);
				sln.alert(CommonTranslations.QANDA_SUCCESS_FORWARDED);
				loadMyQuestions(true);
			},
			error : sln.showAjaxError
		});
	});

    var loadMyQuestions = function(refresh) {
        if (refresh) {
            loadMyQuestionsRequestData.cursor = null;
            myQuestions = [];
        }
        sln.call({
            url : '/common/qanda/myquestions/load',
            type : 'GET',
            data : loadMyQuestionsRequestData,
            success : function(data) {
                if (data.success) {
                    if (data.questions.length < loadMyQuestionsRequestData.count) {
                        $(".load-more-my-questions").hide();
                    } else {
                        $(".load-more-my-questions").show();
                    }
                    loadMyQuestionsRequestData.cursor = data.cursor;

                    $.each(data.questions, function (i, question) {
                        questions[question.id] = question;
                        myQuestions.push(question.id);
                    });

                    var tmp_questions = [];
                    $.each(myQuestions, function (i, mq) {
                        tmp_questions.push(questions[mq]);
                    });

                    var html = $.tmpl(templates.qanda_question_table, {
                        questions : tmp_questions,
                        CommonTranslations : CommonTranslations
                    });
                    $("#qanda_my_questions tbody").empty().append(html);

                    $.each(tmp_questions, function (i, question) {
                        var textThreadCount = "posts";
                        if (question.answers.length == 0) {
                            textThreadCount = "post";
                        }
                        $("#qanda_my_questions tbody tr[question_id=" + question.id + "] .thread-count").text(question.answers.length + 1 + " " + textThreadCount);
                    });

                    $("#qanda_my_questions tbody .view-question").click(viewQuestion);
                } else {
                    sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                }
            },
            error : sln.showAjaxError
        });
    };

    var viewQuestion = function() {
        var question_id = parseInt($(this).closest("tr").attr("question_id"));
        var question = questions[question_id];
        $("#questionDetailModal .modal-header h3").text(question.title);

        var html = $.tmpl(templates.qanda_question_modules, {
            modules : question.modules
        });
        $("#questionDetailModal .modal-header div").empty().append(html);

        question.description_html = sln.htmlize(question.description);
        $.each(question.answers, function (i, answer) {
            question.answers[i].description_html = sln.htmlize(question.answers[i].description);
        });

        var html = $.tmpl(templates.qanda_question_detail, {
            question : question,
            CommonTranslations : CommonTranslations
        });
        $("#questionDetailModal .modal-body div.question-detail-questions").empty().append(html);
        $("#questionDetailModal #reply_question_btn").data("question_id", question_id);
        $("#questionDetailModal").modal("show");
    };

    $("#questionDetailModal #reply_question_btn").click(function() {
        var question_id = $(this).data("question_id");

        var description = $("#questionDetailModal #reply_question_text").val().trim();
        if (!description) {
            sln.alert(CommonTranslations.DESCRIPTION_IS_REQUIRED);
            return;
        }

        sln.call({
            url : "/common/qanda/reply",
            type : "POST",
            data : {
                data : JSON.stringify({
                    question_id : question_id,
                    description : description
                })
            },
            success : function(data) {
                if (!data.success) {
                    return sln.alert(data.errormsg, null, CommonTranslations.ERROR);
                }
                $("#questionDetailModal").modal("hide");
                sln.alert(CommonTranslations.QANDA_SUCCESS_FORWARDED, null, CommonTranslations.SUCCESS);

                if (myQuestions.indexOf(question_id) >= 0) {
                    loadMyQuestions(true);
                }
            },
            error : sln.showAjaxError
        });
    });

    $(".load-more-my-questions").click(function() {
        loadMyQuestions(false);
    });
});
