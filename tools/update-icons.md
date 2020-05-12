# How to update the icons

### Install the necessary tools

#### libsrvg

Linux: `sudo apt-get install librsvg2-bin`

Mac: `sudo port install librsvg`

Windows: https://osspack32.googlecode.com/files/rsvg-convert.exe

#### npm

See https://github.com/nodesource/distributions

#### font-awesome-svg-png

```
npm install -g font-awesome-svg-png
```

### Generate the icons


```
node font-awesome-svg-png --color black --sizes 512,64
```
This will create a folder named 'black' with 2 subfolders (512 and 64) containing the icons

### Rename the icons

Navigate to the folder containing the pngs (e.g. /black/png/512) and execute this command(on ubuntu) or similar:

```
rename 's/^/fa-/' *
```
