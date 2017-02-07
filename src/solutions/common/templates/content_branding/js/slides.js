/*
 * Copyright 2017 Mobicage NV
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
 * @@license_version:1.2@@
 */

var slideVersion = 0;
var galleryIndex = 0;
var linkList = [];
var slidesGalleryIndex = [];
var gallery = null;
var slidesShowContact = false;
    
var setSlides = function() {
    if(rogerthat.user.data.loyalty == undefined) {
        rogerthat.user.data.loyalty = {};
    }
    if(rogerthat.user.data.loyalty.slides == undefined) {
        rogerthat.user.data.loyalty.slides = [];
    }
    
    if(rogerthat.user.data.loyalty.slide_new_order == undefined) {
        rogerthat.user.data.loyalty.slide_new_order = null;
    }
    
    if (!isFlagSet(FUNCTION_SLIDESHOW, tabletFunctions)) {
        console.log("FUNCTION_SLIDESHOW is not enabled");
        return;
    }
    $("#blueimp-gallery").show();
    
    console.log("rogerthat.user.data.loyalty.uuid: " + rogerthat.user.data.loyalty.uuid);
    if (slidesUUID != null && rogerthat.user.data.loyalty.uuid != undefined) {
        console.log("slidesShowContact: " + slidesShowContact);
        console.log("totalNotifications: " + totalNotifications);
        if (slidesShowContact && totalNotifications == 0) {
            console.log("reset slides hiding contact slides");
            if (slidesUUID == rogerthat.user.data.loyalty.uuid && rogerthat.user.data.loyalty.slide_new_order == null) {
                console.log("not showing new order slide");
                return
            }
        } else if (!slidesShowContact && totalNotifications > 0) {
            console.log("reset slides showing contact slides");
            if (slidesUUID == rogerthat.user.data.loyalty.uuid && rogerthat.user.data.loyalty.slide_new_order == null) {
                console.log("not showing new order slide");
                return
            }
        } else if (slidesUUID == rogerthat.user.data.loyalty.uuid) {
            console.log("Ignoring setSlides");
            return;
        }
    }
    if (rogerthat.user.data.loyalty.uuid != undefined) {
        slidesUUID = rogerthat.user.data.loyalty.uuid;
    }
    slideVersion += 1;
    galleryIndex = 0;
    linkList = [];
    slidesGalleryIndex = [];
    
    if (totalNotifications > 0) {
        slidesShowContact = true;
    } else {
        slidesShowContact = false;
    }
    if (rogerthat.user.data.loyalty.slide_new_order == null) {
        console.log("Should show contact but no slide found");
        slidesShowContact = false;
    }
    $.each(rogerthat.user.data.loyalty.slides, function (index, slide) {
        if (slidesShowContact) {
            linkList.push({ title: '',
                href: rogerthat.user.data.loyalty.slide_new_order.full_url,
                type: rogerthat.user.data.loyalty.slide_new_order.content_type,
                thumbnail: rogerthat.user.data.loyalty.slide_new_order.url + "=s50"});
            slidesGalleryIndex.push(null);
        }
        slidesGalleryIndex.push(index);
        linkList.push({ title: '',
            href: slide.full_url,
            type: slide.content_type,
            thumbnail: slide.url + "=s50"});
    });
    gallery = blueimp.Gallery(
            linkList,
            {
                container : '#blueimp-gallery',
                closeOnSlideClick : false,
                closeOnSwipeUpOrDown : false,
                useBootstrapModal : false,
                fullScreen : true,
                preloadRange : 5,
                thumbnailIndicators: false,
                startSlideshow : false,
                index: 0,
                onopen: function () {
                    // Callback function executed when the Gallery is initialized.
                },
                onopened: function () {
                    // Callback function executed when the Gallery has been initialized
                    // and the initialization transition has been completed.
                },
                onslide: function (index, slide) {
                    // Callback function executed on slide change.
                },
                onslideend: function (index, slide) {
                    // Callback function executed after the slide change transition.
                },
                onslidecomplete: function (index, slide) {
                    
                },
                onclose: function () {
                    // Callback function executed when the Gallery is about to be closed.
                },
                onclosed: function () {
                    // Callback function executed when the Gallery has been closed
                    // and the closing transition has been completed.
                }
            }
    );
    
    var scheduleGotoNextSlide = function(slideV) {
        console.log("slideV: " + slideV + " slideVersion: " + slideVersion);
        if (slideV != slideVersion)
            return;
        var tmpGalleryIndex = slidesGalleryIndex[galleryIndex];
        var time = 10 * 1000;
        if (tmpGalleryIndex != null) {
            var s = rogerthat.user.data.loyalty.slides[galleryIndex];
            if (s != undefined) {
                time = s.time * 1000;
            }
        } 
        setTimeout(function(){
            if (linkList.length > galleryIndex + 1) {
                galleryIndex = galleryIndex + 1;
            } else {
                galleryIndex = 0;
            }
            var tmpGalleryIndex_inner = slidesGalleryIndex[galleryIndex];
            var time_inner = 10 * 1000;
            var showFooter = false;
            if (tmpGalleryIndex_inner != null) {
                var s_inner = rogerthat.user.data.loyalty.slides[tmpGalleryIndex_inner];
                if (s_inner != undefined) {
                    time_inner = s_inner.time * 1000;
                    if (s_inner.show_footer == undefined || s_inner.show_footer) {
                        showFooter = true;
                    }
                } else {
                    console.log("ERROR: Did not know slide");
                }
            }
            if (showFooter) {
                $("#osa-overlay").show();
            } else {
                $("#osa-overlay").hide();
            }
            console.log("galleryIndex: " + galleryIndex + " " + time_inner + "ms" + (showFooter ? " showFooter" : " hideFooter" ));
            gallery.slide(galleryIndex, 800);
            scheduleGotoNextSlide(slideV);
        }, time);
    };
    
    setTimeout(function(){
        setSlideHeight();
    }, 100);
    
    scheduleGotoNextSlide(slideVersion);
};

var setSlideHeight = function() {
    var docHeight = $(document).height();
    var docWidth = $(document).width();
    
    if ((docWidth / docHeight) < 1.6) {
        if ($.keyframe.isSupported()) {
            $(".blueimp-gallery>.slides>.slide>.slide-content").css("margin", "0 auto");
            setTimeout(function(){
                var slideHeight = $(".slide-content").height();
                var heightFooter = docHeight - slideHeight;
                if (slideHeight == 0) {
                    setTimeout(function(){
                        setSlideHeight()
                    }, 250);
                    return;
                }
                if (heightFooter > 50) {
                    $.keyframe.define([{
                        name: 'marquee',
                        '0%': {'text-indent': docWidth + 'px'},
                        '100%': {'text-indent': '-' + docWidth + 'px'}
                    }]);
                    var fontSize = 30;
                    if (heightFooter >= 100) {
                        fontSize = 40;
                    }
                    $("#osa-text-slider").css("font-size", fontSize + "px");
                    $("#osa-text-slider").css("height", heightFooter + "px");
                    $("#osa-text-slider").css("padding-top", ((heightFooter - fontSize - 10) / 2) + "px");
                    
                    var appName = rogerthat.service.data.settings.app_name;
                    var name = rogerthat.service.data.settings.name;
                    $("#osa-text-slider").text(Translations.LOYALTY_TERMINAL_FOOTER_TEXT.replace("%(app_name)s", appName).replace("%(name)s", name));
                    $("#osa-text-slider").show();
                } else {
                    $(".blueimp-gallery>.slides>.slide>.slide-content").css("margin", "auto");
                }
                
            }, 500);
        }
    }
};
