(function () {
    ROUTES.forms = router;
    ROUTES.participation = router;
    var element = document.getElementById('dashboard');
    var baseUrl = DEBUG ? 'http://localhost:4200/' : '/static/oca-forms/index.html#/';

    function router(paths) {
        // Only load the iframe once user visits this page to speed up initial page load
        if (element.src) {
            element.contentWindow.postMessage({
                type: 'oca.load_page',
                paths: paths,
            }, DEBUG ? 'http://localhost:4200' : null);
        } else {
            element.src = baseUrl + paths[0];
            element.onload = function () {
                element.contentWindow.postMessage({
                    type: 'oca.set_language',
                    language: LANGUAGE
                }, DEBUG ? 'http://localhost:4200' : null);
            };
        }
        element.style.display = 'block';
    }
})();
