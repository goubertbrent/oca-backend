import { existsSync, lstatSync, readdirSync, readFileSync } from 'fs';
import * as gulp from 'gulp';
import * as util from 'gulp-util';
import { join } from 'path';
import { changeFileManager } from './code_change_tools';
import { Task } from './task';

var isstream = require('isstream');

/**
 * Loads the tasks within the given path.
 * @param {string} path - The path to load the tasks from.
 */
export function loadTasks(path: string): void {
  util.log('Loading tasks folder', util.colors.yellow(path));
  readDir(path, taskname => registerTask(taskname, path));
}

function validateTasks(tasks: any) {
  return Object.keys(tasks)
    .map((taskName: string) => {
      if (!tasks[taskName] ||
        !Array.isArray(tasks[taskName]) ||
        tasks[taskName].some((t: any) => typeof t !== 'string')) {
        return taskName;
      }
      return null;
    }).filter((taskName: string) => !!taskName);
}

function registerTasks(tasks: { [ key: string ]: string[] }) {
  for (const task of Object.keys(tasks)) {
    gulp.task(task, gulp.series(tasks[ task ]));
  }
}

function getInvalidTaskErrorMessage(invalid: string[], file: string) {
  let error = `Invalid configuration in "${file}. `;
  if (invalid.length === 1) {
    error += 'Task';
  } else {
    error += 'Tasks';
  }
  error += ` ${invalid.map((t: any) => `"${t}"`).join(', ')} do not have proper format.`;
  return error;
}

/**
 * Defines complex, composite tasks. The composite tasks
 * are simply a composition of another tasks.
 * Each composite tasks has the following format:
 *
 * "composite_task": ["task1", "task2"]
 *
 * This means that the format should be flat, with no nesting.
 *
 * The existing composite tasks are defined in
 * "tools/config/tasks.json" and can be overriden by
 * editing the composite tasks project configuration.
 *
 * By default it is located in: "tools/config/project.tasks.json".
 *
 * Override existing tasks by simply providing a task
 * name and a list of tasks that this task hould execute.
 *
 * For instance:
 * ```
 * {
 *  "test": [
 *    "build.test",
 *    "mocha.run"
 *  ]
 * }
 * ```
 *
 * Note that the tasks do not support nested objects.
 */
export function loadCompositeTasks(tasksFile: string): void {
  const seedTasks = JSON.parse(readFileSync(tasksFile).toString());
  const invalid = <string[]>validateTasks(seedTasks);
  if (invalid.length) {
    const errorMessage = getInvalidTaskErrorMessage(invalid, tasksFile);
    util.log(util.colors.red(errorMessage));
    process.exit(1);
  }
  registerTasks(seedTasks);
}

function normalizeTask(task: any, taskName: string) {
  if (task instanceof Task) {
    return task;
  }
  if (typeof task === 'function') {
    return new class AnonTask extends Task {
      run(done: any) {
        if (task.length > 0) {
          return task(done);
        }

        const taskReturnedValue = task();
        if (isstream(taskReturnedValue)) {
          return taskReturnedValue;
        }

        done();
      }
    };
  }
  throw new Error(`${taskName} should be instance of the class Task, a function or a class which extends Task.`);
}

/**
 * Registers the task by the given taskname and path.
 * @param {string} taskname - The name of the task.
 * @param {string} path     - The path of the task.
 */
function registerTask(taskname: string, path: string): void {
  const TASK = join(path, taskname);
  gulp.task(taskname, (done: any) => {
    const task = normalizeTask(require(TASK), TASK);

    if (changeFileManager.pristine || task.shallRun(changeFileManager.lastChangedFiles)) {
      const result = task.run(done, changeFileManager.lastChangedFiles);
      if (result && typeof result.catch === 'function') {
        result.catch((e: any) => {
          util.log(`Error while running "${TASK}"`, e);
        });
      }
      return result;
    } else {
      done();
    }
  });
}

/**
 * Reads the files in the given root directory and executes the given callback per found file.
 * @param {string}   root - The root directory to read.
 * @param {function} cb   - The callback to execute per found file.
 */
function readDir(root: string, cb: (taskname: string) => void) {
  if (!existsSync(root)) {
    return;
  }

  walk(root);

  function walk(path: string) {
    const files = readdirSync(path);
    for (const file of files) {
      const curPath = join(path, file);
      if (lstatSync(curPath).isFile() && /\.ts$/.test(file)) {
        const taskname = file.replace(/\.ts$/, '');
        cb(taskname);
      }
    }
  }
}
