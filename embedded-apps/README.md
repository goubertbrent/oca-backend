# Embedded apps

Contains various functionality used in OCA, all made with ionic.

## Running an embedded app in browser

Some of the embedded apps have mocked data services making it possible to run them in browser to test ux/ui
Start them by using any of the following commands:

`npm run start-hoplr`
`npm run start-cirklo`
`npm run start-trash`
`npm run start-participation`
`npm run start-qmatic`


### Tags

(only for 'oca' embedded app)

- events -> tag `agenda` 
- jcc appointments -> tag `__sln__.jcc_appointments`


## Installation

`npm install` should do the trick


## Building

Production build: `npm run build`

Debug build: `npm run build-debug`

This will create a zip file in this directory.

Upload this zip on the server as embedded app using the same 'id' as the zip file name, then create a menu item with a specific tag (see "'oca' app" section for which values for the tag to use) to actually use it.
