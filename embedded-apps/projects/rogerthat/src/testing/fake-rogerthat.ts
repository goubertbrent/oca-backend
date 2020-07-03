// @ts-ignore
import { CameraType } from 'rogerthat-plugin';

const nothing = () => {
};
const rogerthat = {
  // @ts-ignore
  context: func => func({ context: null }),
  app: {
    exit() {
      alert('App closed');
    },
    exitWithResult(result: string) {
      alert('App closed with result: \n' + result);
    },
  },
  api: {
    call: (method: string) => Promise.reject({ error: `Api calls are not supported by fake-rogerthat\n (method: ${method})` }),
    callbacks: {
      resultReceived: nothing,
    },
  },
  callbacks: {
    // @ts-ignore
    ready(callback) {
      callback();
    },
    serviceDataUpdated: nothing,
    userDataUpdated: nothing,
    qrCodeScanned: nothing,
  },
  camera: {
    startScanningQrCode(type: CameraType) {
      return Promise.resolve();
    },
    stopScanningQrCode(type: CameraType) {
      return Promise.resolve();
    },
  },
  user: {
    language: 'nl',
    firstName: 'FirstName',
    lastName: 'LastName',
    data: {},
  },
  system: {
    appId: 'em-be-osa-demo2',
    appVersion: '2.1.5555',
    debug: true,
    colors: {
      primary: '#FF00FF',
    }
  },
  service: {
    data: {},
  },
  menuItem: {
    hashedTag: '__sln__.cirklo',
    label: 'cirklo',
  },
  util: {
    uuid: () => {
      return Math.random().toString();
    },
  },
};
// @ts-ignore
const sha256 = a => a;
// @ts-ignore
window.rogerthat = rogerthat;
// @ts-ignore
window.sha256 = sha256;

export {};
