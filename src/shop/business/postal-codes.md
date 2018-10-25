To rebuild the mapping of postal codes:
- Acquire list of zipcodes and save as postcodes.json in this folder
- execute script:

```javascript

const allCities = require('/.postcodes.json');
const fetch = require('node-fetch');
const fs = require('fs');

async function run() {
    var database = {};  // key: postcode, value: child municipalities
    for (const city of allCities) {
        console.log('Fetching postal codes for ' + city.zip);
        const result = await (await fetch(`https://opzoeken-postcode.be/${city.zip}.json`)).json();
        for (const gemeente of result) {
            if (gemeente.Postcode.postcode_hoofdgemeente === city.zip) {
                database[gemeente.Postcode.postcode_hoofdgemeente] = result.map(r => ({
                    name: r.Postcode.naam_deelgemeente,
                    code: r.Postcode.postcode_deelgemeente,
                    lat: parseFloat(r.Postcode.latitude),
                    lon: parseFloat(r.Postcode.longitude)
                }));
            }
        }
    }
    return database;
}

run().then(result => {
    fs.writeFile('./postal-codes.json', JSON.stringify(result), function () {
        console.log('Done');
    });
});
```

- Change "Beveren" (8791) to "Beveren-Leie" and "Beveren-Waas" to "Beveren"