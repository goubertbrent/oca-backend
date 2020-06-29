// @ts-ignore
import { CameraType } from 'rogerthat-plugin';

const nothing = () => {
};
// @ts-ignore
rogerthat = {
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
    call: nothing,
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
    data: {},
  },
  system: {
    appId: 'em-be-osa-demo2',
    appVersion: '2.1.5555',
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
sha256 = a => a;

export {};
