(function () {
    'use strict';
    var setPasswordForm = $('#setpassword_form');
    var submitting = false;
    setPasswordForm.submit(function (e) {
        if (submitting) {
            return;
        }
        submitting = true;
        e.preventDefault();
        var data = getData();
        sln.showProcessing(TRANSLATIONS.CREATING_SERVICE);
        sln.call({
            method: 'post',
            url: '/customers/signup-password',
            data: JSON.stringify(data),
            success: function (result) {
                sln.hideProcessing();
                submitting = false;
                if (result.success) {
                	window.location = '/';
                } else {
                    sln.alert(result.errormsg, null, TRANSLATIONS.ERROR);
                }
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                sln.hideProcessing();
                submitting = false;
                sln.showAjaxError(XMLHttpRequest, textStatus, errorThrown);
            }
        });
    });

    function getData() {
        return {
            email: $('#login_email').val(),
            data: $('#login_data').val(),
            password: $('#password').val(),
            password_confirm: $('#password_confirm').val(),
        };
    }
})();
