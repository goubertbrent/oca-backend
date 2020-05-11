var validationFieldIsRequired = function run(result, rogerthat) {
    var hasValue = false;
    if (result.values) {
        hasValue = result.values.length > 0;
    } else {
        if (typeof result === 'number') {
            hasValue = result !== 0;
        } else {
            hasValue = !!(result.value || '').toString().trim();
        }
    }
    if (!hasValue) {
        return rogerthat.util.translate('%(errorMessage)');
    }
    return true;
};

var validationSnippets = {
    required: {
        name: 'Required field',
        code: validationFieldIsRequired.toString(),
        description: 'Checks if the input value is not empty',
        placeholders: {
            errorMessage: {
                name: 'Error message',
                defaultValue: 'This is a required field'
            }
        }
    },
};
