import { copy, remove } from 'fs-extra';
import * as gulp from 'gulp';
import * as gutil from 'gulp-util';
import * as gulpWatch from 'gulp-watch';
import { join } from 'path';
import { config } from '../config/config';

const deleteEmpty = require('delete-empty');
const debounce = require('lodash.debounce');

if (process.platform === 'darwin') {
  try {
    require('fsevents');
  } catch (ignored) {
    throw new Error('Could not require fsevents, please execute `npm install` again.');
  }
}

/**
 * Copies files from build roots over to the 'build' folder.
 * Ensures changes are in sync with the source root by copying changed files and removing deleted files.
 */
export function watch() {
  const debouncedClean = debounce(cleanEmptyFolders, 200);
  return function () {
    let paths: string[] = [
      '!' + config.BUILD_ROOT,
      ...config.SOURCE_ROOTS.map(root => join(root, '**')),
      ...config.TEMP_FILES.map(temp => '!' + temp) ];

    gulpWatch(paths, async (e) => {
      if (e.path.endsWith('.yaml')) {
        gulp.task('merge.yaml')(() => {
          gutil.log('Rebuild yaml files');
        });
      } else {
        const sourceRoot = config.SOURCE_ROOTS.find(root => e.path.startsWith(root));
        const buildFolderPath = e.path.replace(sourceRoot, config.BUILD_ROOT);
        switch (e.event) {
          case 'add':
            try {
              await copy(e.path, buildFolderPath);
              gutil.log(gutil.colors.green(`Created file ${buildFolderPath}`));
            } catch (e) {
              gutil.log(gutil.colors.blue(`Could not copy file ${e.path}: ` + e.message));
            }
            break;
          case 'unlink':
            await remove(buildFolderPath);
            gutil.log(gutil.colors.red(`Removed file ${buildFolderPath}`));
            if (buildFolderPath.endsWith('.py')) {
              await remove(buildFolderPath.replace('.py', '.pyc'));
            }
            debouncedClean();
            break;
          case 'change':
            try {
              await copy(e.path, buildFolderPath);
              gutil.log(gutil.colors.yellow(`Updated file ${buildFolderPath}`));
            } catch (e) {
              gutil.log(gutil.colors.blue(`Could not copy file ${e.path}: ` + e.message));
            }
            break;
        }
      }
    });
  };
}

export function cleanEmptyFolders() {
  return deleteEmpty.sync(config.BUILD_ROOT);
}
