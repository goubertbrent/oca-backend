# Deploy instructions

- Install nodejs https://nodejs.org/en/download/package-manager/
- Install bower and gulp `sudo npm install -g bower gulp`
- Run `npm install` in this folder.
- Run `bower install` if it failed in the previous step
- Run `gulp build --project {projectname}` to build the project that has changed

# Developer instructions

- Run all of the above commands
- Run `gulp watch --project {projectname}` in this folder to build the files when changes are detected
- Run `gulp karma --project {projectname}` to run the unit tests. Other options are karma-fast (test without rebuilding) and karma-watch (run tests as soon as changes are detected)

