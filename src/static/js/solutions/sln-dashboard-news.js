(function () {
    'use strict';
    var NEWS = null;
    ROUTES['dashboard-news'] = router;

    function router() {
        showNews();
    }

    function getNews() {
        if (NEWS) {
            renderDashboardNews(NEWS);
        } else {
            sln.call({
                url: '/common/dashboard-news',
                success: function (data) {
                    NEWS = data;
                    renderDashboardNews(NEWS);
                }
            });
        }
    }

    function renderDashboardNews(newsItems) {
        // Do not show the news page if no news was found.
        // This can happen when there are no articles yet in the user his language.
        if (newsItems.length === 0 && !userClickedBeforeNewsLoaded) {
            window.location.hash = '#';
            $('#topmenu').find('a:eq(1)').click();
            return;
        }
        var html = $.tmpl(templates['dashboard-news/news_item'], {
            news: newsItems.map(function (item) {
                return Object.assign({}, item, {creation_time: sln.format(new Date(item.creation_time))});
            })
        });
        $('#dashboard-news').html(html);
        $('.youtube-player').each(function () {
            var $this = $(this);
            var ytId = $this.attr('data-yt-id');
            $this.click(function () {
                // open popup with this video
                var iframe = $('<iframe height="100%" frameborder="0" allowfullscreen>');
                iframe.attr('src', 'https://www.youtube.com/embed/' + ytId + '?autoplay=1&showinfo=1&fs=1');
                $('#video-yt-container').html(iframe);
                $("#video-popup").show()
                    .modal('show')
                    .on('hidden', function () {
                        $('#video-yt-container').empty();
                    });
            });
        });
    }

    function showNews() {
        getNews();
    }

})();
