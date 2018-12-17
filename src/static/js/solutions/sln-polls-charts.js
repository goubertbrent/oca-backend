function PollChartsWrapper() {
}

PollChartsWrapper.prototype.drawChart = function (containerId, title, chartData) {
    var wrapper = new google.visualization.ChartWrapper({
        chartType: 'BarChart',
        dataTable: google.visualization.arrayToDataTable(chartData),
        options: {
            title: title,
            legend: {
                position: 'none'
            },
            animation: {duration: 1000, easing: 'out', startup: true}
        },
        containerId: containerId,
    });
    wrapper.draw();
}

var PollCharts = new PollChartsWrapper();
