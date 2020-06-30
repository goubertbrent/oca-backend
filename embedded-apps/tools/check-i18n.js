import {readdirSync, readFileSync, realpathSync} from 'fs';
import {readdir} from "fs/promises"
import {dirname, join} from "path"


const projects = ['hoplr', 'oca'];
const currentFolder = realpathSync(dirname(''));

checkProjects(projects, join(currentFolder, '..', 'projects'));

function dotify(obj) {
  const res = {};

  function recurse(obj, current) {
    for (const key of Object.keys(obj)) {
      const value = obj[key];
      const newKey = (current ? current + '.' + key : key);  // joined key with dot
      if (typeof value === 'object') {
        recurse(value, newKey);  // it's a nested object, so do it again
      } else {
        res[newKey] = value;  // it's not an object, so set the property
      }
    }
  }

  recurse(obj);
  return res;
}

async function checkProjects(projects, baseDir) {
  for (const project of projects) {
    const dir = join(baseDir, project, 'src', 'assets', 'i18n');
    const files = readdirSync(dir);
    const sourceKeys = new Set();
    for (const filename of files) {
      const path = join(dir, filename);
      const translations = dotify(JSON.parse(readFileSync(path).toString()));
      const translationKeys = Object.keys(translations);
      for await (const sourceFile of ls(join(baseDir, project, 'src'))) {
        if (sourceFile.endsWith('.ts') || sourceFile.endsWith('.html')) {
          const content = readFileSync(sourceFile).toString();
          for (const key of translationKeys) {
            if (content.includes(key)) {
              sourceKeys.add(key);
            }
          }
        }
      }
      const unusedKeys = translationKeys.filter(k => !sourceKeys.has(k));
      if (unusedKeys.length) {
        const lang = filename.split('.')[0];
        console.log(`[${project}] Some translations keys are not used for language ${lang}:`, unusedKeys);
      }
    }
  }
}

async function* ls(path = '.') {
  yield path;
  for (const dirent of await readdir(path, {withFileTypes: true}))
    if (dirent.isDirectory()) {
      yield* ls(join(path, dirent.name));
    } else {
      yield join(path, dirent.name);
    }
}
