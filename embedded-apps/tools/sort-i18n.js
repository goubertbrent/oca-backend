import {readdirSync, readFileSync, realpathSync, writeFileSync} from 'fs'
import {dirname, join} from 'path'

const currentFolder = realpathSync(dirname(''));

function sortTranslations(file) {
  const translations = JSON.parse(readFileSync(file).toString());
  const result = JSON.stringify(sortObject(translations), null, 2);
  writeFileSync(file, result);
}

function sortObject(object) {
  let sortedObj = {};
  const keys = Object.keys(object).sort();

  for (let key of keys) {
    if (object[key] instanceof Object) {
      sortedObj[key] = sortObject(object[key]);
    } else {
      sortedObj[key] = object[key];
    }
  }
  return sortedObj;
}

const projects = ['hoplr', 'oca', 'cirklo'];
for (const project of projects) {
  const dir = join(currentFolder, '..', 'projects', project, 'src', 'assets', 'i18n');
  const files = readdirSync(dir);
  for (const file of files) {
    const path = join(dir, file);
    sortTranslations(path);
    console.log(`Sorted ${path}`);
  }
}
