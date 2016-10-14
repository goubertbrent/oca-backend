var path = require('path');
// 'dependencies' are dependencies which have both .js and .min.js files available (in the same folder)
// These dependencies must be present in the /static/libs folder
var projects = {
    admin: {
        indexPageFolder: '../src/shop/admin/',
        dependencies: [
            'angular/angular',
            'angular-route/angular-route',
            'angular-animate/angular-animate',
            'angular-aria/angular-aria',
            'angular-sanitize/angular-sanitize',
            'angular-resource/angular-resource',
            'angular-messages/angular-messages',
            'angular-ui-router/release/angular-ui-router',
            'angular-translate/angular-translate',
            'angular-local-storage/dist/angular-local-storage',
            'angular-translate-handler-log/angular-translate-handler-log',
            'angular-material/angular-material',
            'source-map/dist/source-map'
        ]
    }
};
exports.ROOT = path.normalize(__dirname + '/..');
exports.projects = projects;