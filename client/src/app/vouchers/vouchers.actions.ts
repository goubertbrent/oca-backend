import { Action } from '@ngrx/store';
import { ErrorAction } from '../shared/errors/errors';
import { ExportVoucherServices, VoucherProviderId, VoucherService, VouchersServiceList } from './vouchers';

export enum VouchersActionTypes {
  GET_SERVICES = '[Vouchers] Get services',
  GET_SERVICES_SUCCESS = '[Vouchers] Get services success',
  GET_SERVICES_FAILED = '[Vouchers] Get services failed',
  SAVE_VOUCHER_PROVIDER = '[Vouchers] Save voucher provider',
  SAVE_VOUCHER_SETTINGS_SUCCESS = '[Vouchers] Save voucher provider success',
  SAVE_VOUCHER_FAILED = '[Vouchers] Save voucher provider failed',
  EXPORT_VOUCHER_SERVICES = '[Vouchers] Export voucher services',
  EXPORT_VOUCHER_SERVICES_SUCCESS = '[Vouchers] Export voucher services success',
  EXPORT_VOUCHER_SERVICES_FAILED = '[Vouchers] Export voucher services failed',
}

export class GetServicesAction implements Action {
  readonly type = VouchersActionTypes.GET_SERVICES;

  constructor(public payload: { organizationType: number, cursor: string | null, sort: string; pageSize: number }) {
  }
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

export class SaveVoucherSettingsAction implements Action {
  readonly type = VouchersActionTypes.SAVE_VOUCHER_PROVIDER;

  constructor(public payload: { serviceEmail: string, providers: VoucherProviderId[] }) {
  }
}

export class SaveVoucherSettingsSuccessAction implements Action {
  readonly type = VouchersActionTypes.SAVE_VOUCHER_SETTINGS_SUCCESS;

  constructor(public payload: { serviceEmail: string; service: VoucherService }) {
  }
}

export class SaveVoucherSettingsFailedAction implements ErrorAction {
  readonly type = VouchersActionTypes.SAVE_VOUCHER_FAILED;

  constructor(public error: string) {
  }
}

export class ExportVoucherServicesAction implements Action {
  readonly type = VouchersActionTypes.EXPORT_VOUCHER_SERVICES;
}

export class ExportVoucherServicesSuccessAction implements Action {
  readonly type = VouchersActionTypes.EXPORT_VOUCHER_SERVICES_SUCCESS;

  constructor(public payload: ExportVoucherServices) {
  }
}

export class ExportVoucherServicesFailedAction implements ErrorAction {
  readonly type = VouchersActionTypes.EXPORT_VOUCHER_SERVICES_FAILED;

  constructor(public error: string) {
  }
}

export type VouchersActions =
  GetServicesAction
  | GetServicesSuccessAction
  | GetServicesFailedAction
  | SaveVoucherSettingsAction
  | SaveVoucherSettingsSuccessAction
  | SaveVoucherSettingsFailedAction
  | ExportVoucherServicesAction
  | ExportVoucherServicesSuccessAction
  | ExportVoucherServicesFailedAction;

