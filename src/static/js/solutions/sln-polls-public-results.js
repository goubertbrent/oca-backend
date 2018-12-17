$(function() {
    var container = $('#results_container');

    function renderResult() {
        google.charts.load('current', {packages: ['bar']});
        google.charts.setOnLoadCallback(render);

        function render() {
            container.append(`
                <h3 style="text-align: center">${currentPoll.name}</h3>
            `)
            $.each(currentPoll.questions, function(questionId, question) {
                container.append(`
                    <div id="results_${questionId}"></div>
                `)

                var chartData = [['', '', { role: 'annotation' }]];
                $.each(question.choices, function(j, choice) {
                    chartData.push([choice.text, choice.count, choice.count]);
                });

                PollCharts.drawChart(`results_${questionId}`, question.text, chartData);
            });
        }
    }


    if (!currentPoll.answers_collected) {
        $('.answer-pending').show();
    } else {
        renderResult();
    }
});
