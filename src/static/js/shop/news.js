(function () {
    var NEWS = null;
    var currentArticle;

    var supportedLanguages = [
        {code: 'nl', name: 'Dutch'},
        {code: 'en', name: 'English'},
        {code: 'fr', name: 'French'},
        {code: 'de', name: 'German'},
        {code: 'ro', name: 'Romanian'},
        {code: 'es', name: 'Spanish'},
        {code: 'ru', name: 'Russian'},
    ];

    $(document).ready(function () {
        renderNews();
    });

    function getNews(callback) {
        if (NEWS) {
            callback(NEWS);
        } else {
            sln.call({
                url: '/internal/shop/rest/dashboard-news',
                success: function (data) {
                    NEWS = data;
                    callback(NEWS);
                }
            });
        }
    }

    function renderNews() {
        getNews(function (news) {
            // Hide the create/ edit
            $('#put-news').hide();
            var html = $.tmpl(JS_TEMPLATES['dashboard-news/news_list'], {
                news: news.map(n => ({...n, creation_time: sln.format(new Date(n.creation_time))}))
            });
            $('#news-container').show().html(html);
            $('#create-news').click(() => renderNewsForm());
            $('.update-dashboard-news').click(function () {
                var newsId = $(this).data('dashboard-news-id');
                renderNewsForm(newsId);
            });
            $('.delete-dashboard-news').click(function () {
                var newsId = $(this).data('dashboard-news-id');
                deleteNews(newsId);
            });
        });

    }

    function updateNews() {
        var newsValues = getNewsFormValues();
        newsValues.id = currentArticle.id;
        var method = currentArticle.id ? 'put' : 'post';
        var url = '/internal/shop/rest/dashboard-news' + (currentArticle.id ? '/' + currentArticle.id : '');
        sln.call({
                url: url,
                method: method,
                data: JSON.stringify(newsValues),
                success: function (data) {
                    NEWS = [...NEWS.filter(n => n.id !== data.id), data];
                    renderNews();
                }
            }
        );
    }

    function deleteNews(id) {
        var newsId = parseInt(id);
        if (!isNaN(newsId)) {
            sln.call({
                url: '/internal/shop/rest/dashboard-news/' + id,
                method: 'delete',
                success: function () {
                    NEWS = NEWS.filter(function (n) {
                        return n.id !== newsId;
                    });
                    renderNews();
                }
            });
        }
    }

    function renderNewsPreview() {
        var html = $.tmpl(JS_TEMPLATES['dashboard-news/news_preview'], {
            article: currentArticle,
            date: sln.format(new Date())
        });
        $('#news-preview').html(html);
    }

    function renderNewsForm(newsId) {
        $('#news-container').hide();
        $('#put-news').show();
        if (newsId) {
            currentArticle = NEWS.filter(n => n.id === newsId)[0];
            if (currentArticle) {
                renderNewsPreview();
            }
        } else {
            currentArticle = {
                media_type: 1,
                language: 'nl',
                content: '',
                media: '',
                id: null
            };
        }
        var formParams = {
            edit: !!newsId,
            article: currentArticle,
            languages: supportedLanguages
        };
        var html = $.tmpl(JS_TEMPLATES['dashboard-news/news_form'], formParams);
        $('#news-form').html(html)
            .find('input[id*="news-"], textarea')
            .keyup(function () {
                var $this = $(this);
                if ($this.val() === '') {
                    $this.parent().parent().addClass('error').removeClass('success');
                } else {
                    $this.parent().parent().removeClass('error').addClass('success');
                }
                var id = currentArticle.id;
                currentArticle = getNewsFormValues();
                currentArticle.id = id;
                renderNewsPreview();
            });
        $('#news-type').change(function () {
            var $this = $(this);
            var yt = $('#news-yt');
            var img = $('#news-image');
            switch ($this.val()) {
                case '1':
                    yt.removeClass('hide');
                    img.addClass('hide');
                    break;
                case '2':
                    yt.addClass('hide');
                    img.removeClass('hide');
                    break;
            }


        });
        $('#news-submit').click(updateNews);
        $('#dashboard-news-overview').click(renderNews);
    }

    function getYoutubeIdFromUrl(url) {
        var matches = url.match(/^.*(youtu.be\/|v\/|embed\/|watch\?|youtube.com\/user\/[^#]*#([^\/]*?\/)*)\??v?=?([^#\&\?]*).*/);
        return matches ? matches[3] : '';
    }

    function getNewsFormValues() {
        var type = parseInt($('#news-type').val());
        var media;
        if (type === 1) {
            media = getYoutubeIdFromUrl($('#news-youtubeUrl').val());
        } else {
            media = $('#news-imageUrl').val();
        }
        return {
            language: $('#news-language').val(),
            media_type: type,
            title: $('#news-title').val(),
            media: media,
            content: $('#news-content').val(),
        };
    }
})();
