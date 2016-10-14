var args = require('./util').args,
    consts = require('./const'),
    projectName = args.project,
    project = consts.projects[projectName];
if (!project) {
    throw new Error('Invalid project specified: ' + projectName);
}
module.exports = {
    jsFiles: [
        projectName + '/**/*.js',
        '!' + projectName + '/**/*.spec.js',
        'common/**/*.js',
        '!common/**/*.spec.js'
    ],
    projectName: projectName,
    destFolder: '../src/static/' + projectName,
    indexPageFolder: project.indexPageFolder,
    project: project,
    htmlMinOptions: {
        empty: true,
        quotes: true,
        collapseWhitespace: true,
        conservativeCollapse: true,
        removeComments: true,
        removeTagWhitespace: true,
        removeScriptTypeAttributes: true,
        minifyCSS: true
    },
    debug: !args.online || args.debug
};


