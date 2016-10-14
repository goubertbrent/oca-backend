/**
 * Created by lucas on 2/7/16.
 */
var gulp = require('gulp'),
    livereload = require('gulp-livereload'),
    config = require('../config'),
    htmlMin = require('gulp-htmlmin'),
    watch = require('gulp-watch');

exports.dependencies = ['build'];
exports.task = function () {
    // Watch .html files
    watch(config.projectName + '/**/*.html')
        .pipe(htmlMin(config.htmlMinOptions))
        .pipe(gulp.dest(config.destFolder + '/html'))
        .pipe(livereload());

    // Watch .styl files
    watch(config.projectName + '/**/*.styl', function () {
        gulp.start('build-styles');
    });

    // Watch .js files
    watch(config.projectName + '/**/*.js', function () {
        gulp.start('build-js');
    });

    // Watch 'common' modules
    watch('common/**/*.js', function () {
        gulp.start('build-js');
    });

    gulp.watch(config.projectName + '/' + config.projectName + '.html', ['build-index']);

    // Don't reload entire page for CSS files.
    gulp.watch(config.destFolder + '/css/' + config.projectName + '.min.css').on('change', livereload.changed);

    // Create LiveReload server
    livereload.listen();
};