/**
 * Created by lucas on 2/17/16.
 */
var gulp = require('gulp'),
    config = require('../config'),
    livereload = require('gulp-livereload'),
    rename = require('gulp-rename'),
    htmlReplace = require('gulp-html-replace'),
    htmlMin = require('gulp-htmlmin');

exports.task = function () {
    var js = '',
        channelSrc = 'https://talkgadget.google.com/talkgadget/channel.js';
    if (config.debug) {
        channelSrc = '/_ah/channel/jsapi';
    }
    var dependencies = config.project.dependencies;
    var extension = (config.debug ? '.js' : '.min.js');
    for (var i = 0; i < dependencies.length; i++) {
        js += '<script src="/static/libs/' + dependencies[i] + extension + '"></script>';
    }
    js += '<script src="/static/' + config.projectName + '/js/' + config.projectName + '.min.js"></script>';
    var css = '<link rel="stylesheet" href="/static/' + config.projectName + '/css/' + config.projectName + '.min.css">';
    return gulp.src(config.projectName + '/' + config.projectName + '.html')
        .pipe(htmlReplace({
            channel: {
                src: null,
                tpl: '<script src="' + channelSrc + '"></script>'
            },
            js: {
                src: null,
                tpl: js
            },
            css: {
                src: null,
                tpl: css
            }
        }))
        .pipe(htmlMin(config.htmlMinOptions))
        .pipe(rename({suffix: '.min'}))
        .pipe(gulp.dest(config.indexPageFolder))
        .pipe(livereload());
};