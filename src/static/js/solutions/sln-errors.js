function SolutionsErrorHandler(options) {
    options = options || {};

    this.errors = new Map();
    this.flushTimestamp = 0;
    this.flushInterval = options.flushInterval || 5000;
    this.logToConsole = options.logToConsole || false;

    setInterval(this.flushErrors.bind(this), this.flushInterval);
}

SolutionsErrorHandler.prototype = {
    getErrorMessage: function(error, sourceUrl, line, column) {
        var stack_trace;
        var errorMsg = '';

        if (error instanceof Error) {
            try {
                errorMsg = error.description || error.message;
                stack_trace = '\n' + printStackTrace({
                    guess: true,
                    e: error
                }).join('\n');
            } catch(err) {
                stack_trace = 'Failed to print stack trace! \nOriginal error: ' + description;
            }
        } else {
            stack_trace = error || '';
        }

        if (sourceUrl) {
            errorMsg += '\nin ' + sourceUrl;
            if (line && column) {
                errorMsg += ' at line ' + line + ':' + column;
            }
        }

        errorMsg += stack_trace;
        return errorMsg;
    },

    logError: function(description, error, sourcUrl, line, column) {
        var fullErrorMessage = this.getErrorMessage(error, sourcUrl, line, column);

        if (this.errors.has(fullErrorMessage)) {
            return;
        }

        if (this.logToConsole) {
            console.error(fullErrorMessage);
        }

        var now = sln.nowUTC();
        if (!this.flushTimestamp) {
            this.flushTimestamp = now;
            this.sendError(description, fullErrorMessage, now);
        } else  {
            this.errors.set(fullErrorMessage, {
                timestamp: now,
                description: description
            });
        }
    },

    sendError: function(description, error, timestamp) {
        sln.call({
            url: SLN_CONSTS.LOG_ERROR_URL,
            type: 'post',
            data: {
                description: description,
                errorMessage: error,
                timestamp: timestamp,
                user_agent: navigator.userAgent
            },
            success: function() {
            },
            error: function() {
            }
        });
    },

    flushErrors: function() {
        if (!this.errors.size) {
            return;
        }

        var timeDiff = this.flushTimestamp ? sln.nowUTC() - this.flushTimestamp : 0;
        if (timeDiff <= this.flushInterval / 1000) {
            return;
        }

        this.errors.forEach(function(value, error) {
            this.sendError(value.description, error, value.timestamp);
            this.errors.delete(error);
        }.bind(this));

        this.flushTimestamp = sln.nowUTC();
    },
}
