(function () {
    ROUTES.forms = router;
    ROUTES.participation = router;
    ROUTES.news = router;
    var element = document.getElementById('dashboard');
    var baseUrl = DEBUG ? 'http://localhost:4300/' : '/static/client/index.html#/';
    var topMenu = $('#topmenu');
    window.addEventListener('message', function (e) {
        if (e.data && e.data.type === 'oca.set_navigation') {
            window.history.pushState(null, null, '#' + e.data.path);
            setNavigation(e.data.path);
        }
    });

    function router(paths) {
        // Only load the iframe once user visits this page to speed up initial page load
        var origin =  DEBUG ? 'http://localhost:4300' : window.location.origin;
        if (element.src) {
            element.contentWindow.postMessage({
                'type': 'oca.load_page',
                'paths': paths
            }, origin);
        } else {
            element.src = baseUrl + paths[0];
            element.onload = function () {
                element.contentWindow.postMessage({
                    'type': 'oca.set_language',
                    'language': LANGUAGE
                }, origin);
            };
        }
        element.style.display = 'block';
    }

    function setNavigation(menu) {
        topMenu.find('li[menu]').removeClass('active');
        topMenu.find('li[menu=' + menu + ']').addClass('active');
    }
})();
