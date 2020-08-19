import { Action } from '@ngrx/store';
import { ErrorAction } from '@oca/web-shared';
import { CirkloSettings, VoucherService, VouchersServiceList } from './vouchers';

export enum VouchersActionTypes {
  GET_SERVICES = '[Vouchers] Get services',
  GET_SERVICES_SUCCESS = '[Vouchers] Get services success',
  GET_SERVICES_FAILED = '[Vouchers] Get services failed',
  WHITELIST_VOUCHER_SERVICE = '[Vouchers] Whitelist voucher service',
  WHITELIST_VOUCHER_SERVICE_SUCCESS = '[Vouchers] Save voucher provider success',
  WHITELIST_VOUCHER_SERVICE_FAILED = '[Vouchers] Save voucher provider failed',
  GET_CIRKLO_SETTINGS = '[Vouchers] Get cirklo settings',
  GET_CIRKLO_SETTINGS_SUCCESS = '[Vouchers] Get cirklo settings success',
  GET_CIRKLO_SETTINGS_FAILED = '[Vouchers] Get cirklo settings failed',
  SAVE_CIRKLO_SETTINGS = '[Vouchers] Save cirklo settings',
  SAVE_CIRKLO_SETTINGS_SUCCESS = '[Vouchers] Save cirklo settings success',
  SAVE_CIRKLO_SETTINGS_FAILED = '[Vouchers] Save cirklo settings failed',
}

export class GetServicesAction implements Action {
  readonly type = VouchersActionTypes.GET_SERVICES;
}

export class GetServicesSuccessAction implements Action {
  readonly type = VouchersActionTypes.GET_SERVICES_SUCCESS;

  constructor(public payload: VouchersServiceList) {
  }
}

export class GetServicesFailedAction implements ErrorAction {
  readonly type = VouchersActionTypes.GET_SERVICES_FAILED;

  constructor(public error: string) {
  }
}

export class WhitelistVoucherServiceAction implements Action {
  readonly type = VouchersActionTypes.WHITELIST_VOUCHER_SERVICE;

  constructor(public payload: { id: string, email: string, accepted: boolean }) {
  }
}

export class WhitelistVoucherServiceSuccessAction implements Action {
  readonly type = VouchersActionTypes.WHITELIST_VOUCHER_SERVICE_SUCCESS;

  constructor(public payload: { id: string; email: string, service: VoucherService }) {
  }
}

export class WhitelistVoucherServiceFailedAction implements ErrorAction {
  readonly type = VouchersActionTypes.WHITELIST_VOUCHER_SERVICE_FAILED;

  constructor(public error: string) {
  }
}

export class GetCirkloSettingsAction implements Action {
  readonly type = VouchersActionTypes.GET_CIRKLO_SETTINGS;
}

export class GetCirkloSettingsCompleteAction implements Action {
  readonly type = VouchersActionTypes.GET_CIRKLO_SETTINGS_SUCCESS;

  constructor(public payload: CirkloSettings) {
  }
}

export class GetCirkloSettingsFailedAction implements ErrorAction {
  readonly type = VouchersActionTypes.GET_CIRKLO_SETTINGS_FAILED;

  constructor(public error: string) {
  }
}

export class SaveCirkloSettingsAction implements Action {
  readonly type = VouchersActionTypes.SAVE_CIRKLO_SETTINGS;

  constructor(public payload: CirkloSettings) {
  }
}

export class SaveCirkloSettingsCompleteAction implements Action {
  readonly type = VouchersActionTypes.SAVE_CIRKLO_SETTINGS_SUCCESS;

  constructor(public payload: CirkloSettings) {
  }
}

export class SaveCirkloSettingsFailedAction implements ErrorAction {
  readonly type = VouchersActionTypes.SAVE_CIRKLO_SETTINGS_FAILED;

  constructor(public error: string) {
  }
}

export type VouchersActions =
  GetServicesAction
  | GetServicesSuccessAction
  | GetServicesFailedAction
  | WhitelistVoucherServiceAction
  | WhitelistVoucherServiceSuccessAction
  | WhitelistVoucherServiceFailedAction
  | GetCirkloSettingsAction
  | GetCirkloSettingsCompleteAction
  | GetCirkloSettingsFailedAction
  | SaveCirkloSettingsAction
  | SaveCirkloSettingsCompleteAction
  | SaveCirkloSettingsFailedAction;

