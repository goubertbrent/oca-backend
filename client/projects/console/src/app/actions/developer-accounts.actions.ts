import { Action } from '@ngrx/store';
import { ApiRequestStatus } from '../../../framework/client/rpc';
import { CreateDeveloperAccountPayload, DeveloperAccount } from '../interfaces';

export const enum DeveloperAccountsActionTypes {
  GET_DEVELOPER_ACCOUNTS = '[RCC:dev accounts] Get developer accounts',
  GET_DEVELOPER_ACCOUNTS_COMPLETE = '[RCC:dev accounts] Get developer accounts complete',
  GET_DEVELOPER_ACCOUNTS_FAILED = '[RCC:dev accounts] Get developer accounts failed',
  CLEAR_DEVELOPER_ACCOUNT = '[RCC:dev accounts] Clear developer account',
  GET_DEVELOPER_ACCOUNT = '[RCC:dev accounts] Get developer account',
  GET_DEVELOPER_ACCOUNT_COMPLETE = '[RCC:dev accounts] Get developer account complete',
  GET_DEVELOPER_ACCOUNT_FAILED = '[RCC:dev accounts] Get developer account failed',
  CREATE_DEVELOPER_ACCOUNT = '[RCC:dev accounts] Create developer account',
  CREATE_DEVELOPER_ACCOUNT_COMPLETE = '[RCC:dev accounts] Create developer account complete',
  CREATE_DEVELOPER_ACCOUNT_FAILED = '[RCC:dev accounts] Create developer account failed',
  UPDATE_DEVELOPER_ACCOUNT = '[RCC:dev accounts] Update developer account',
  UPDATE_DEVELOPER_ACCOUNT_COMPLETE = '[RCC:dev accounts] Update developer account complete',
  UPDATE_DEVELOPER_ACCOUNT_FAILED = '[RCC:dev accounts] Update developer account failed',
  REMOVE_DEVELOPER_ACCOUNT = '[RCC:dev accounts] Remove developer account',
  REMOVE_DEVELOPER_ACCOUNT_COMPLETE = '[RCC:dev accounts] Remove developer account complete',
  REMOVE_DEVELOPER_ACCOUNT_FAILED = '[RCC:dev accounts] Remove developer account failed',
}

export class GetDeveloperAccountsAction implements Action {
  readonly type = DeveloperAccountsActionTypes.GET_DEVELOPER_ACCOUNTS;
}

export class GetDeveloperAccountsCompleteAction implements Action {
  readonly type = DeveloperAccountsActionTypes.GET_DEVELOPER_ACCOUNTS_COMPLETE;

  constructor(public payload: Array<DeveloperAccount>) {
  }
}

export class GetDeveloperAccountsFailedAction implements Action {
  readonly type = DeveloperAccountsActionTypes.GET_DEVELOPER_ACCOUNTS_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class ClearDeveloperAccountAction implements Action {
  readonly type = DeveloperAccountsActionTypes.CLEAR_DEVELOPER_ACCOUNT;
}

export class GetDeveloperAccountAction implements Action {
  readonly type = DeveloperAccountsActionTypes.GET_DEVELOPER_ACCOUNT;

  constructor(public payload: { id: number }) {
  }
}

export class GetDeveloperAccountCompleteAction implements Action {
  readonly type = DeveloperAccountsActionTypes.GET_DEVELOPER_ACCOUNT_COMPLETE;

  constructor(public payload: DeveloperAccount) {
  }
}

export class GetDeveloperAccountFailedAction implements Action {
  readonly type = DeveloperAccountsActionTypes.GET_DEVELOPER_ACCOUNT_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class CreateDeveloperAccountAction implements Action {
  readonly type = DeveloperAccountsActionTypes.CREATE_DEVELOPER_ACCOUNT;

  constructor(public payload: CreateDeveloperAccountPayload) {
  }
}

export class CreateDeveloperAccountCompleteAction implements Action {
  readonly type = DeveloperAccountsActionTypes.CREATE_DEVELOPER_ACCOUNT_COMPLETE;

  constructor(public payload: DeveloperAccount) {
  }
}

export class CreateDeveloperAccountFailedAction implements Action {
  readonly type = DeveloperAccountsActionTypes.CREATE_DEVELOPER_ACCOUNT_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdateDeveloperAccountAction implements Action {
  readonly type = DeveloperAccountsActionTypes.UPDATE_DEVELOPER_ACCOUNT;

  constructor(public payload: DeveloperAccount) {
  }
}

export class UpdateDeveloperAccountCompleteAction implements Action {
  readonly type = DeveloperAccountsActionTypes.UPDATE_DEVELOPER_ACCOUNT_COMPLETE;

  constructor(public payload: DeveloperAccount) {
  }
}

export class UpdateDeveloperAccountFailedAction implements Action {
  readonly type = DeveloperAccountsActionTypes.UPDATE_DEVELOPER_ACCOUNT_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class RemoveDeveloperAccountAction implements Action {
  readonly type = DeveloperAccountsActionTypes.REMOVE_DEVELOPER_ACCOUNT;

  constructor(public payload: DeveloperAccount) {
  }
}

export class RemoveDeveloperAccountCompleteAction implements Action {
  readonly type = DeveloperAccountsActionTypes.REMOVE_DEVELOPER_ACCOUNT_COMPLETE;

  constructor(public payload: DeveloperAccount) {
  }
}

export class RemoveDeveloperAccountFailedAction implements Action {
  readonly type = DeveloperAccountsActionTypes.REMOVE_DEVELOPER_ACCOUNT_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export type DeveloperAccountsActions
  = GetDeveloperAccountsAction
  | GetDeveloperAccountsCompleteAction
  | GetDeveloperAccountsFailedAction
  | GetDeveloperAccountAction
  | GetDeveloperAccountCompleteAction
  | GetDeveloperAccountFailedAction
  | ClearDeveloperAccountAction
  | CreateDeveloperAccountAction
  | CreateDeveloperAccountCompleteAction
  | CreateDeveloperAccountFailedAction
  | UpdateDeveloperAccountAction
  | UpdateDeveloperAccountCompleteAction
  | UpdateDeveloperAccountFailedAction
  | RemoveDeveloperAccountAction
  | RemoveDeveloperAccountCompleteAction
  | RemoveDeveloperAccountFailedAction;
