/*
 * Copyright 2017 GIG Technology NV
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

var news = [];
var currentArticle = {
    news_type: 1
};

var supportedLanguages = [
    {code: 'nl', name: 'Dutch', default: true},
    {code: 'en', name: 'English'},
    {code: 'fr', name: 'French'},
    {code: 'de', name: 'German'},
    {code: 'ro', name: 'Romanian'},
    {code: 'es', name: 'Spanish'},
    {code: 'ru', name: 'Russian'}
];

$(document).ready(function () {
    loadNews(renderNews);
});

function loadNews(callback) {
    if (news.length) {
        callback();
    } else {
        sln.call({
            url: '/internal/shop/rest/news/all',
            success: function (data) {
                news = data;
                callback();
            }
        });
    }
}

function renderNews() {
    // Hide the create/ edit
    $('#put-news').hide();
    $.each(news, function (i, n) {
        n.dateFormatted = sln.format(new Date(n.datetime * 1000));
    });
    var html = $.tmpl(JS_TEMPLATES['news/news_list'], {
        news: news
    });
    $('#news-container').show().html(html);

}

function putNews() {
    var newsValues = getNewsFormValues();
    newsValues.news_id = currentArticle.news_id;
    sln.call({
            url: '/internal/shop/rest/news/put',
            method: 'post',
            data: {
                data: JSON.stringify(newsValues)
            },
            success: function (data) {
                if (data.errormsg) {
                    showError(data.errormsg);
                } else {
                    news = news.filter(function (n) {
                        return n.news_id !== data.news.news_id;
                    });
                    news.push(data.news);
                    window.location.hash = '#/news';
                }
            }
        }
    );
}

function deleteNews(id) {
    var newsId = parseInt(id);
    if (!isNaN(newsId)) {
        sln.call({
            url: '/internal/shop/rest/news/delete',
            data: {news_id: newsId},
            success: function () {
                news = news.filter(function (n) {
                    return n.news_id !== newsId;
                });
                window.location.hash = '#/news';
            }
        });
    }
}

function renderNewsPreview() {
    var html = $.tmpl(JS_TEMPLATES['news/news_preview'], {
        article: currentArticle,
        date: sln.format(new Date())
    });
    $('#news-preview').html(html);
}

function renderNewsForm(newsId) {
    $('#news-container').hide();
    $('#put-news').show();
    if (newsId) {
        currentArticle = news.filter(function (n) {
            return n.news_id == newsId;
        })[0];
        if (currentArticle) {
            renderNewsPreview();
        }
    } else {
        currentArticle = {news_type: 1}
    }
    var html = $.tmpl(JS_TEMPLATES['news/news_form'], {
        edit: newsId ? true : false,
        article: currentArticle,
        languages: supportedLanguages
    });
    $('#news-form').html(html)
        .find('input[id*="news-"], textarea')
        .keyup(function () {
            var $this = $(this);
            if ($this.val() === '') {
                $this.parent().parent().addClass('error').removeClass('success');
            } else {
                $this.parent().parent().removeClass('error').addClass('success');
            }
            var id = currentArticle.news_id;
            currentArticle = getNewsFormValues();
            currentArticle.news_id = id;
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
    $('#news-submit').click(putNews);
}

function getYoutubeIdFromUrl(url) {
    var matches = url.match(/^.*(youtu.be\/|v\/|embed\/|watch\?|youtube.com\/user\/[^#]*#([^\/]*?\/)*)\??v?=?([^#\&\?]*).*/);
    return matches ? matches[3] : '';
}

function getNewsFormValues() {
    var yt = $('#news-youtubeUrl').val();
    return {
        language: $('#news-language').val(),
        news_type: parseInt($('#news-type').val()),
        title: $('#news-title').val(),
        youtube_id: yt ? getYoutubeIdFromUrl(yt) : '',
        image_url: $('#news-imageUrl').val(),
        content: $('#news-content').val()
    };
}
