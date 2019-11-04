import { Action } from '@ngrx/store';
import { CameraType, QrCodeScannedContent, RogerthatError } from 'rogerthat-plugin';
import { ServiceData, UserData } from './rogerthat';

export const enum RogerthatActionTypes {
  SET_USER_DATA = '[rogerthat] Set user data',
  SET_SERVICE_DATA = '[rogerthat] Set service data',
  SCAN_QR_CODE = '[rogerthat] Scan QR code',
  SCAN_QR_CODE_STARTED = '[rogerthat] Scan QR code started',
  SCAN_QR_CODE_UPDATE = '[rogerthat] Scan QR code update',
  SCAN_QR_CODE_FAILED = '[rogerthat] Scan QR code failed',
}

export class SetUserDataAction implements Action {
  readonly type = RogerthatActionTypes.SET_USER_DATA;

  constructor(public payload: UserData) {
  }
}

export class SetServiceDataAction implements Action {
  readonly type = RogerthatActionTypes.SET_SERVICE_DATA;

  constructor(public payload: ServiceData) {
  }
}

export class ScanQrCodeAction implements Action {
  readonly type = RogerthatActionTypes.SCAN_QR_CODE;

  constructor(public payload: CameraType) {
  }
}

export class ScanQrCodeStartedAction implements Action {
  readonly type = RogerthatActionTypes.SCAN_QR_CODE_STARTED;
}

export class ScanQrCodeUpdateAction implements Action {
  readonly type = RogerthatActionTypes.SCAN_QR_CODE_UPDATE;

  constructor(public payload: QrCodeScannedContent) {
  }
}

export class ScanQrCodeFailedAction implements Action {
  readonly type = RogerthatActionTypes.SCAN_QR_CODE_FAILED;

  constructor(public error: string) {
  }
}


export type RogerthatActions = SetUserDataAction
  | SetServiceDataAction
  | ScanQrCodeAction
  | ScanQrCodeStartedAction
  | ScanQrCodeUpdateAction
  | ScanQrCodeFailedAction;

