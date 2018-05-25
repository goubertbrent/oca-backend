(function () {
    var acceptCheckbox = $('#accept-checkbox');
    var checkboxContainer = $('#checkbox-container');
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
