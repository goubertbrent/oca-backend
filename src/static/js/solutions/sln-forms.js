(function () {
    ROUTES.forms = router;

    function router(hash) {
        // Only load the iframe once user visits this page to speed up initial page load
        var element = document.getElementById('forms-container');
        if (!element.src) {
            element.src = '/static/oca-forms/index.html';
            element.onload = function () {
                element.contentWindow.postMessage({
                    type: 'oca.set_language',
                    language: LANGUAGE
                });
            };
        }
    }

})();
