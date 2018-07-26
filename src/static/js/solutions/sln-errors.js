/*
 * Copyright 2018 Mobicage NV
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
 * @@license_version:1.3@@
 */

function SolutionsErrorHandler(options) {
    options = options || {};

    this.errors = {};
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

        if (this.errors[fullErrorMessage]) {
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
            this.errors[fullErrorMessage] = {
                timestamp: now,
                description: description
            };
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
        if (!Object.keys(this.errors).length) {
            return;
        }

        var timeDiff = this.flushTimestamp ? sln.nowUTC() - this.flushTimestamp : 0;
        if (timeDiff <= this.flushInterval / 1000) {
            return;
        }

        Object.keys(this.errors).forEach(function(error) {
            var value = this.errors[error];
            this.sendError(value.description, error, value.timestamp);
            delete this.errors[error];
        }.bind(this));

        this.flushTimestamp = sln.nowUTC();
    },
}
