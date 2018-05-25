(function () {
    var acceptCheckbox = $('#accept-checkbox');
    var checkboxContainer = $('#checkbox-container');
    var tosElem = $('#terms-of-use');
    acceptCheckbox.on('input', function () {
    });

    tosElem.on('scroll', function () {
        if (tosElem[0].scrollHeight - tosElem.scrollTop() <= tosElem.outerHeight()) {
            acceptCheckbox.prop('disabled', false);
            tosElem.off('scroll');
            $('#read-toc-to-continue').remove();
        }
    });
    $('#terms-form').on('submit', function (e) {
        if (!acceptCheckbox.prop('checked')) {
            e.preventDefault();
            showError();
        }
    });

    function showError() {
        checkboxContainer.addClass('has-error');
        checkboxContainer.find('.help-block').show();
    }
})();
