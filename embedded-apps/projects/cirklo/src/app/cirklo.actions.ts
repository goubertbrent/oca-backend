import { Action } from '@ngrx/store';
import { AddVoucherResponse, CirkloMerchantsList, CirkloVoucher, CirkloVouchersList, VoucherTransactionsList } from './cirklo';


export const enum CirkloActionTypes {
  GET_VOUCHERS = '[Cirklo] Get vouchers',
  GET_VOUCHERS_SUCCESS = '[Cirklo] Get vouchers success',
  GET_VOUCHERS_FAILED = '[Cirklo] Get vouchers failed',
  ADD_VOUCHER = '[Cirklo] Add voucher',
  ADD_VOUCHER_SUCCESS = '[Cirklo] Add voucher success',
  ADD_VOUCHER_FAILED = '[Cirklo] Add voucher failed',
  CONFIRM_DELETE_VOUCHER = '[Cirklo] Confirm delete voucher',
  CONFIRM_DELETE_VOUCHER_CANCELLED = '[Cirklo] Confirm delete voucher cancelled',
  DELETE_VOUCHER = '[Cirklo] Delete voucher',
  DELETE_VOUCHER_SUCCESS = '[Cirklo] Delete voucher success',
  DELETE_VOUCHER_FAILED = '[Cirklo] Delete voucher failed',
  GET_VOUCHER_TRANSACTIONS = '[Cirklo] Get voucher transactions',
  GET_VOUCHER_TRANSACTIONS_SUCCESS = '[Cirklo] Get voucher transactions success',
  GET_VOUCHER_TRANSACTIONS_FAILED = '[Cirklo] Get voucher transactions failed',
  GET_MERCHANTS = '[Cirklo] Get merchants',
  GET_MERCHANTS_SUCCESS = '[Cirklo] Get merchants success',
  GET_MERCHANTS_FAILED = '[Cirklo] Get merchants failed',
}

export class LoadVouchersAction implements Action {
  readonly type = CirkloActionTypes.GET_VOUCHERS;
}

export class LoadVouchersSuccessAction implements Action {
  readonly type = CirkloActionTypes.GET_VOUCHERS_SUCCESS;

  constructor(public payload: CirkloVouchersList) {
  }
}

export class LoadVouchersFailedAction implements Action {
  readonly type = CirkloActionTypes.GET_VOUCHERS_FAILED;

  constructor(public error: string) {
  }
}

export class AddVoucherAction implements Action {
  readonly type = CirkloActionTypes.ADD_VOUCHER;

  constructor(public payload: { qrContent: string }) {
  }
}

export class AddVoucherSuccessAction implements Action {
  readonly type = CirkloActionTypes.ADD_VOUCHER_SUCCESS;

  constructor(public payload: AddVoucherResponse) {
  }
}

export class AddVoucherFailedAction implements Action {
  readonly type = CirkloActionTypes.ADD_VOUCHER_FAILED;

  constructor(public error: string) {
  }
}

export class ConfirmDeleteVoucherAction implements Action {
  readonly type = CirkloActionTypes.CONFIRM_DELETE_VOUCHER;

  constructor(public payload: { id: string }) {
  }
}

export class ConfirmDeleteVoucherCancelledAction implements Action {
  readonly type = CirkloActionTypes.CONFIRM_DELETE_VOUCHER_CANCELLED;

  constructor(public payload: { id: string }) {
  }
}

export class DeleteVoucherAction implements Action {
  readonly type = CirkloActionTypes.DELETE_VOUCHER;

  constructor(public payload: { id: string }) {
  }
}

export class DeleteVoucherSuccessAction implements Action {
  readonly type = CirkloActionTypes.DELETE_VOUCHER_SUCCESS;

  constructor(public payload: { id: string }) {
  }
}

export class DeleteVoucherFailedAction implements Action {
  readonly type = CirkloActionTypes.DELETE_VOUCHER_FAILED;

  constructor(public error: string) {
  }
}

export class GetVoucherTransactionsAction implements Action {
  readonly type = CirkloActionTypes.GET_VOUCHER_TRANSACTIONS;

  constructor(public payload: { id: string }) {
  }
}

export class GetVoucherTransactionsCompleteAction implements Action {
  readonly type = CirkloActionTypes.GET_VOUCHER_TRANSACTIONS_SUCCESS;

  constructor(public payload: VoucherTransactionsList) {
  }
}

export class GetVoucherTransactionsFailedAction implements Action {
  readonly type = CirkloActionTypes.GET_VOUCHER_TRANSACTIONS_FAILED;

  constructor(public error: string) {
  }
}

export class GetMerchantsAction implements Action {
  readonly type = CirkloActionTypes.GET_MERCHANTS;

  constructor(public payload: { cursor?: string }) {
  }
}

export class GetMerchantsCompleteAction implements Action {
  readonly type = CirkloActionTypes.GET_MERCHANTS_SUCCESS;

  constructor(public payload: CirkloMerchantsList) {
  }
}

export class GetMerchantsFailedAction implements Action {
  readonly type = CirkloActionTypes.GET_MERCHANTS_FAILED;

  constructor(public error: string) {
  }
}

export type CirkloActions =
  LoadVouchersAction
  | LoadVouchersSuccessAction
  | LoadVouchersFailedAction
  | AddVoucherAction
  | AddVoucherSuccessAction
  | AddVoucherFailedAction
  | ConfirmDeleteVoucherAction
  | ConfirmDeleteVoucherCancelledAction
  | DeleteVoucherAction
  | DeleteVoucherSuccessAction
  | DeleteVoucherFailedAction
  | GetVoucherTransactionsAction
  | GetVoucherTransactionsCompleteAction
  | GetVoucherTransactionsFailedAction
  | GetMerchantsAction
  | GetMerchantsCompleteAction
  | GetMerchantsFailedAction;
