import * as crypto from 'crypto';
import { existsSync, readFileSync, writeFileSync } from 'fs';
import * as gutil from 'gulp-util';
import * as yaml from 'js-yaml';
import { join } from 'path';
import { config } from '../config/config';

const mergeWith = require('lodash.mergewith');

/**
 * Merges app.yaml, index.yaml, queue.yaml and cron.yaml files from every plugin into one file.
 * Hashes the contents of the result to avoid re-writing the file
 * This avoids the `Detected file changes` in the appengine devserver)
 */
export = () => {
  const hashes: { [key: string]: string | null } = {
    'app.yaml': null,
    'index.yaml': null,
    'queue.yaml': null,
    'cron.yaml': null,
  };
  const files = [];
  for (const sourceRoot of config.SOURCE_ROOTS) {
    for (const filename of Object.keys(hashes)) {
      const path = join(sourceRoot, filename);
      if (existsSync(path)) {
        files.push(path);
      }
    }
  }
  for (const [filename, oldHash] of Object.entries(hashes)) {
    const outData = {};
    const filePaths = files.filter(f => f.endsWith(filename));
    for (const file of filePaths) {
      const inputData = yaml.safeLoad(readFileSync(file, 'utf-8'));
      mergeYamlFile(inputData, outData, file.endsWith('app.yaml'));
    }
    const result = yaml.safeDump(outData, {noCompatMode: true, lineWidth: 120});
    const outputPath = join(config.BUILD_ROOT, filename);
    if (oldHash === null) {
      hashes[filename] = existsSync(outputPath) ? getHash(readFileSync(outputPath, 'utf-8')) : '';
    }
    const newHash = getHash(result);
    if (hashes[filename] !== newHash) {
      writeFileSync(outputPath, result);
      hashes[filename] = newHash;
    }
  }

  function getHash(input: string) {
    const hash = crypto.createHash('sha1');
    hash.setEncoding('hex');
    hash.write(input);
    hash.end();
    return <string>hash.read();
  }

  function mergeYamlFile(inputData: any, outData: any, isAppYaml: boolean) {
    if (isAppYaml) {
      mergeAppYaml(outData, inputData);
    } else {
      mergeWith(outData, inputData, merger);
    }
  }

  function merger(objValue: any, srcValue: any) {
    if (Array.isArray(objValue)) {
      return objValue.concat(srcValue);
    }
    return undefined;
  }

  function mergeAppYaml(outData: any, data: any) {
    const keys = Object.keys(data);
    for (const key of keys) {
      let value = data[key];
      if (Array.isArray(value) && outData[key]) {
        value = value.concat(outData[key]);
      }
      if (key === 'handlers') {
        value = getSortedHandlers(value);
      }
      outData[key] = value;
    }
    return outData;
  }

  function getSortedHandlers(originalHandlers: any[]) {
    const handlersToKeep = [];
    const handlersToSort = [];
    let newHandlers;

    for (const handler of originalHandlers) {
      if (handler.url.endsWith('/.*')) {
        handlersToSort.push(handler);
      } else {
        handlersToKeep.push(handler);
      }
    }
    newHandlers = handlersToKeep;
    for (let i = 0; i < handlersToSort.length; i++) {
      const handler: any = handlersToSort[i];
      const handlerUrl = handler.url.substring(0, handler.url.length - 2); // trim the .* from the end of the url string
      let didntBreak = true;
      for (const secondHandler of handlersToSort.slice(i + 1)) {
        const secondHandlerUrl = secondHandler.url.substring(0, secondHandler.url.length - 2);  // trim the .* from the
                                                                                                // end of the url
                                                                                                // string
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
