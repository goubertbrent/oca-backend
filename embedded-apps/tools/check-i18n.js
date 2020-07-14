import {readdirSync, readFileSync, realpathSync} from 'fs';
import {readdir} from 'fs/promises'
import {dirname, join} from 'path'


const projects = ['hoplr', 'oca', 'cirklo', 'trash-calendar'];
const currentFolder = realpathSync(dirname(''));

checkProjects(projects, join(currentFolder, '..', 'projects')).catch(err => {
  console.error(err);
  return process.exit(1);
});

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

function undotify(o) {
  var oo = {}, t, parts, part;
  for (let k of Object.keys(o)) {
    t = oo;
    parts = k.split('.');
    var key = parts.pop();
    while (parts.length) {
      part = parts.shift();
      t = t[part] = t[part] || {};
    }
    t[key] = o[k];
  }
  return oo;
}

async function checkProjects(projects, baseDir) {
  const warnings = [];
  const errors = [];
  for (const project of projects) {
    const dir = join(baseDir, project, 'src', 'assets', 'i18n');
    const files = readdirSync(dir);
    const sourceKeys = new Set();
    const keysInLangs = new Map();
    for (const filename of files) {
      const path = join(dir, filename);
      const translations = dotify(JSON.parse(readFileSync(path).toString()));
      const translationKeys = Object.keys(translations);
      keysInLangs.set(filename, translationKeys);
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

        warnings.push(`[${project}] Some translations keys are not used for language ${lang}: ${unusedKeys.join(', ')}`);
        for (const key of unusedKeys) {
          delete translations[key];
        }
        console.log(`[${project}] Fixed translations:\n${JSON.stringify(undotify(translations))}`);
      }
    }
    const expectedKeys = keysInLangs.get('en.json');
    for (const filename of files) {
      const actualKeys = keysInLangs.get(filename);
      const missingKeys = expectedKeys.filter(key => !actualKeys.includes(key));
      if (missingKeys.length) {
        const lang = filename.split('.')[0];
        errors.push(`[${project}] Language ${lang} is missing some translations: ${missingKeys.join(', ')}`);
      }
    }
  }
  if (warnings.length) {
    console.warn(warnings.join('\n'));
  }
  if (errors.length) {
    throw new Error(errors.join('\n'));
  }
}

async function* ls(path = '.') {
  yield path;
  for (const entry of await readdir(path, {withFileTypes: true}))
    if (entry.isDirectory()) {
      yield* ls(join(path, entry.name));
    } else {
      yield join(path, entry.name);
    }
}
