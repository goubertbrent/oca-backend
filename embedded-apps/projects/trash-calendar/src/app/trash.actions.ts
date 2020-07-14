import { Action } from '@ngrx/store';
import { GetStreetsResult, SaveAddressRequest, SaveNotificationsRequest, TrashHouseNumber } from './trash';


export const enum TrashActionTypes {
  GetStreets = '[Trash] Get streets',
  GetStreetsSuccess = '[Trash] Get streets success',
  GetStreetsFailure = '[Trash] Get streets failed',
  GetHouseNumbers = '[Trash] Get house numbers',
  GetHouseNumbersSuccess = '[Trash] Get house numbers success',
  GetHouseNumbersFailure = '[Trash] Get house numbers failed',
  SaveAddress = '[Trash] Save address',
  SaveAddressSuccess = '[Trash] Save address success',
  SaveAddressFailure = '[Trash] Save address failed',
  SaveNotifications = '[Trash] Save notifications',
  SaveNotificationsSuccess = '[Trash] Save notifications success',
  SaveNotificationsFailure = '[Trash] Save notifications failed',
}

export class GetStreets implements Action {
  readonly type = TrashActionTypes.GetStreets;
}

export class GetStreetsSuccess implements Action {
  readonly type = TrashActionTypes.GetStreetsSuccess;

  constructor(public payload: GetStreetsResult) {
  }
}

export class GetStreetsFailure implements Action {
  readonly type = TrashActionTypes.GetStreetsFailure;

  constructor(public error: string) {
  }
}

export class GetHouseNumbers implements Action {
  readonly type = TrashActionTypes.GetHouseNumbers;

  constructor(public payload: { streetnumber: number; streetname: string }) {
  }
}

export class GetHouseNumbersSuccess implements Action {
  readonly type = TrashActionTypes.GetHouseNumbersSuccess;

  constructor(public payload: TrashHouseNumber[]) {
  }
}

export class GetHouseNumbersFailure implements Action {
  readonly type = TrashActionTypes.GetHouseNumbersFailure;

  constructor(public error: string) {
  }
}

export class SaveAddress implements Action {
  readonly type = TrashActionTypes.SaveAddress;

  constructor(public payload: SaveAddressRequest) {
  }
}

export class SaveAddressSuccess implements Action {
  readonly type = TrashActionTypes.SaveAddressSuccess;
}

export class SaveAddressFailure implements Action {
  readonly type = TrashActionTypes.SaveAddressFailure;

  constructor(public error: string) {
  }
}

export class SaveNotifications implements Action {
  readonly type = TrashActionTypes.SaveNotifications;

  constructor(public payload: SaveNotificationsRequest) {
  }
}

export class SaveNotificationsSuccess implements Action {
  readonly type = TrashActionTypes.SaveNotificationsSuccess;
}

export class SaveNotificationsFailure implements Action {
  readonly type = TrashActionTypes.SaveNotificationsFailure;

  constructor(public error: string) {
  }
}


export type TrashActions =
  GetStreets
  | GetStreetsSuccess
  | GetStreetsFailure
  | GetHouseNumbers
  | GetHouseNumbersSuccess
  | GetHouseNumbersFailure
  | SaveAddress
  | SaveAddressSuccess
  | SaveAddressFailure
  | SaveNotifications
  | SaveNotificationsSuccess
  | SaveNotificationsFailure;
