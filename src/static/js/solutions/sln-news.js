/*
 * Copyright 2016 Mobicage NV
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
 * @@license_version:1.1@@
 */
(function () {
    'use strict';
    var newsInitialized = false;

    init();

    function init() {
        ROUTES['news'] = router;
    }

    function router() {
        showNews();
    }

    function initializeNews() {
        sln.call({
            url: '/common/news/all',
            success: function (newsItems) {
                // Do not show the news page if no news was found.
                // This can happen when there are no articles yet in the user his language.
                if (newsItems.length === 0) {
                    window.location.hash = '#';
                    if (!userClickedBeforeNewsLoaded) {
                        $('#topmenu').find('a:first').click();
                    }
                }
                $.each(newsItems, function (i, n) {
                    n.dateFormatted = sln.format(new Date(n.datetime * 1000));
                });
                var html = $.tmpl(templates['news/news_item'], {
                    news: newsItems
                });
                $('#news-container').html(html);
                $('.youtube-player').each(function () {
                    var $this = $(this);
                    var ytId = $this.attr('data-yt-id');
                    $this.click(function () {
                        // open popup with this video
                        var iframe = $('<iframe height="100%" frameborder="0" allowfullscreen>');
                        iframe.attr('src', '//www.youtube.com/embed/' + ytId + '?autoplay=1&showinfo=1&fs=1');
                        //$this.html(iframe);
                        $('#video-yt-container').html(iframe);
                        $("#video-popup").show()
                            .modal('show')
                            .on('hidden', function () {
                                $('#video-yt-container').empty();
                            });
                    });
                });

                $('.coaching-sessions, .news').slick({
                    slidesToShow: 3,
                    slidesToScroll: 1,
                    dots: true,
                    infinite: false
                });
            }
        });
    }

    function showNews() {
        $("#topmenu li").removeClass("active");
        $('.page').hide();
        $('#newspage').show();
        if (!newsInitialized) {
            initializeNews();
            newsInitialized = true;
        }
    }

})();