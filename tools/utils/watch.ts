import { copy, mkdirp, remove } from 'fs-extra';
import * as gulp from 'gulp';
import * as gutil from 'gulp-util';
import { join } from 'path';
import { config } from '../config/config';

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
  return function () {
    let paths: string[] = [
      '!' + config.BUILD_ROOT,
      ...config.SOURCE_ROOTS.map(root => join(root, '**')) ];

    gulp.watch(paths, { ignored: config.IGNORED_FILES })
      .on('change', async (file) => await processChange('change', file))
      .on('add', async (file) => await processChange('add', file))
      .on('unlink', async (file) => await processChange('unlink', file))
      .on('addDir', async (file) => await processChange('addDir', file))
      .on('unlinkDir', async (file) => await processChange('unlinkDir', file));
  };
}

async function processChange(event: 'add' | 'unlink' | 'change' | 'addDir' | 'unlinkDir', path: string) {
  if (path.endsWith('.yaml')) {
    gulp.task('merge.yaml')(() => {
      gutil.log('Rebuild yaml files');
    });
  } else {
    const sourceRoot = config.SOURCE_ROOTS.find(root => path.startsWith(root));
    const buildFolderPath = path.replace(sourceRoot, config.BUILD_ROOT);
    switch (event) {
      case 'add':
        try {
          await copy(path, buildFolderPath);
          gutil.log(gutil.colors.green(`Created file ${buildFolderPath}`));
        } catch (e) {
          gutil.log(gutil.colors.blue(`Could not copy file ${path}: ` + e.message));
        }
        break;
      case 'unlink':
        await remove(buildFolderPath);
        gutil.log(gutil.colors.red(`Removed file ${buildFolderPath}`));
        if (buildFolderPath.endsWith('.py')) {
          await remove(buildFolderPath.replace('.py', '.pyc'));
        }
        break;
      case 'change':
        try {
          await copy(path, buildFolderPath);
          gutil.log(gutil.colors.yellow(`Updated file ${buildFolderPath}`));
        } catch (e) {
          gutil.log(gutil.colors.blue(`Could not copy file ${path}: ` + e.message));
        }
        break;
      case 'addDir':
        try {
          await mkdirp(buildFolderPath);
          gutil.log(gutil.colors.green(`Created directory ${buildFolderPath}`));
        } catch (e) {
          gutil.log(gutil.colors.blue(`Could not create directory ${buildFolderPath}: ` + e.message));
        }
        break;
      case 'unlinkDir':
        try {
          await remove(buildFolderPath);
          gutil.log(gutil.colors.red(`Removed directory ${buildFolderPath}`));
        } catch (e) {
          gutil.log(gutil.colors.blue(`Could not remove directory ${buildFolderPath}: ` + e.message));
        }
        break;
    }
  }
}
