const fs = require('fs');
const join = require('path').join;

function sortTranslations(file) {
  const translations = JSON.parse(fs.readFileSync(file).toString());
  const result = JSON.stringify(sortObject(translations), null, 2);
  fs.writeFileSync(file, result);
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

const path = join(__dirname, '..', 'src', 'assets', 'i18n');
const files = fs.readdirSync(path);
for (const file of files) {
  sortTranslations(join(path, file));
}
