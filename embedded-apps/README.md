# Our city app embedded app

Contains various functionality used in OCA.

### 'oca' app
- events -> tag `__sln__.q_matic` 
- q-matic appointments ->  tag `agenda`
- jcc appointments -> tag `__sln__.jcc_appointments`

### 'hoplr' app

Contains functionality related to hoplr, and nothing else. The only tag supported is `__sln__.hoplr`.


## Installation

`npm install` should do the trick


## Building

Production build: `npm run build`

Debug build: `npm run build-debug`

This will create a zip file in this directory.

Upload this zip on the server as embedded app with id 'oca' or 'hoplr' (depending on what project you're building), then create a menu item with a specific tag (see first section for which values for the tag to use) to actually use it.
