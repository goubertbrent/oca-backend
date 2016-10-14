var karma = require('karma').server;
var ROOT = require('../const').ROOT;
var util = require('../util');
var Server = require('karma').Server;
var args = util.args;
var config = {
    singleRun: false,
    autoWatch: true,
    projectName: args.project,
    configFile: ROOT + '/config/karma.conf.js',
    browsers: ['PhantomJS2']
};

// Make full build of JS and CSS
exports.dependencies = ['build'];

exports.task = function (done) {
    var server = new Server(config, done);
    server. start();
};
