import { Action } from '@ngrx/store';
import { CameraType, GetNewsStreamItemsRequestTO, GetNewsStreamItemsResponseTO, QrCodeScannedContent } from 'rogerthat-plugin';
import { ServiceData, UserData } from './rogerthat';

export const enum RogerthatActionTypes {
  SET_USER_DATA = '[rogerthat] Set user data',
  SET_SERVICE_DATA = '[rogerthat] Set service data',
  SCAN_QR_CODE = '[rogerthat] Scan QR code',
  SCAN_QR_CODE_STARTED = '[rogerthat] Scan QR code started',
  SCAN_QR_CODE_UPDATE = '[rogerthat] Scan QR code update',
  SCAN_QR_CODE_FAILED = '[rogerthat] Scan QR code failed',
  GET_NEWS_STREAM_ITEMS = '[rogerthat] Get news stream items',
  GET_NEWS_STREAM_ITEMS_COMPLETE = '[rogerthat] Get news stream items complete',
  GET_NEWS_STREAM_ITEMS_FAILED = '[rogerthat] Get news stream items failed',
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

export class GetNewsStreamItemsAction implements Action {
  readonly type = RogerthatActionTypes.GET_NEWS_STREAM_ITEMS;

  constructor(public payload: GetNewsStreamItemsRequestTO) {
  }
}

export class GetNewsStreamItemsCompleteAction implements Action {
  readonly type = RogerthatActionTypes.GET_NEWS_STREAM_ITEMS_COMPLETE;

  constructor(public payload: GetNewsStreamItemsResponseTO) {
  }
}

export class GetNewsStreamItemsFailedAction implements Action {
  readonly type = RogerthatActionTypes.GET_NEWS_STREAM_ITEMS_FAILED;

  constructor(public error: string) {
  }
}


export type RogerthatActions = SetUserDataAction
  | SetServiceDataAction
  | ScanQrCodeAction
  | ScanQrCodeStartedAction
  | ScanQrCodeUpdateAction
  | ScanQrCodeFailedAction
  | GetNewsStreamItemsAction
  | GetNewsStreamItemsCompleteAction
  | GetNewsStreamItemsFailedAction;

