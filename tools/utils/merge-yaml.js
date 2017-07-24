'use strict';

const path = require('path');
const through = require('through2');
const yaml = require('js-yaml');
const gutil = require('gulp-util');
const PluginError = gutil.PluginError;
const _ = {
    merge: require('lodash.merge'),
    mergeWith: require('lodash.mergewith')
};
const File = gutil.File;

// basically a copy from https://github.com/ivansky/gulp-yaml-merge/blob/master/index.js with the exception of adding a custom merger.
module.exports = (file, opt) => {
    if (!file) {
        throw new PluginError('merge-yaml', 'Missing file option for merge-yam');
    }

    opt = opt || {};

    let loadOptions = opt.load || {};
    // noCompatMode ensure ancestor: yes doesn't become ancestor: 'yes'
    const dumpOptions = opt.dump || {noCompatMode: true};
    let isAppYaml = !!opt.appYaml;

    let latestFile;
    let outData = {};

    if (typeof file !== 'string' && typeof file.path !== 'string') {
        throw new PluginError('gulp-yaml-merge', 'Missing path in file options for gulp-yaml-merge');
    }

    function bufferContents(file, enc, cb) {
        // ignore empty files
        if (file.isNull()) {
            cb();
            return;
        }

        // we don't do streams (yet)
        if (file.isStream()) {
            this.emit('error', new PluginError('merge-yaml', 'Streaming not supported'));
            cb();
            return;
        }

        latestFile = file;

        // pass file path for yaml error handler
        loadOptions = _.merge(loadOptions, {filename: file.path});

        let data;
        try {
            data = yaml.safeLoad(file.contents, loadOptions);
        } catch (err) {
            this.emit('error', new PluginError('merge-yaml', err));
            cb();
            return;
        }
        if (isAppYaml) {
            outData = _.mergeWith(outData, data, mergeAppYaml);
        } else {
            outData = _.mergeWith(outData, data, merger);
        }

        cb();
    }

    function endStream(cb) {
        let outFile;
        if (!latestFile) {
            cb();
            return;
        }
        if (typeof file === 'string') {
            outFile = latestFile.clone({contents: false});
            outFile.path = path.join(latestFile.base, file);
        } else {
            outFile = new File(file);
        }

        outFile.contents = new Buffer(yaml.safeDump(outData, dumpOptions));

        this.push(outFile);

        cb();
    }

    return through.obj(bufferContents, endStream);

    function merger(objValue, srcValue) {
        if (Array.isArray(objValue)) {
            return objValue.concat(srcValue);
        }
        return undefined;
    }

    /**
     * Ensures the least significant routes are placed at the bottom of the app.yaml file
     * @param objValue
     * @param srcValue
     * @returns {*}
     */
    function mergeAppYaml(objValue, srcValue) {
        if (objValue && objValue.length && objValue[0].url && objValue[0].script) {
            objValue = getSortedHandlers([...objValue, ...srcValue]);
            return objValue;
        }
        return undefined;
    }

    function getSortedHandlers(originalHandlers) {
        let handlersToKeep = [],
            handlersToSort = [],
            newHandlers;

        for (let handler of originalHandlers) {
            if (handler.url.endsWith('/.*')) {
                handlersToSort.push(handler);
            }
            else {
                handlersToKeep.push(handler);
            }
        }
        newHandlers = handlersToKeep;
        for (let i = 0; i < handlersToSort.length; i++) {
            let handler = handlersToSort[i];
            let handlerUrl = handler.url.substring(0, handler.url.length - 2); // trim the .* from the end of the url string
            let didntBreak = true;
            for (let secondHandler of handlersToSort.slice(i + 1)) {
                let secondHandlerUrl = secondHandler.url.substring(0, secondHandler.url.length - 2);  // trim the .* from the end of the url string
                // We can't have duplicates!!
                if (handlerUrl === secondHandlerUrl) {
                    gutil.log(gutil.colors.red(`Duplicate url found in 2 handlers:\n${handler.url}\n${secondHandler.url}\n`));
                }
                // Check if the url we're comparing too contains the first url
                // Eg: /test/123/ contains /test/
                if (secondHandlerUrl.startsWith(handlerUrl)) {
                    // We need to move handler_url after second_handler_url, so we move it to the end of the list
                    handlersToSort.push(handler);
                    didntBreak = false;
                    break;  // No need to keep looping, we already know we need to move this handler
                }
            }
            if (didntBreak) {
                newHandlers.push(handler);
            }
        }
        return newHandlers;
    }

};
