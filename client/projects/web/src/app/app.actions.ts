import { Action } from '@ngrx/store';
import { ErrorAction, PublicAppInfo } from '@oca/web-shared';

export enum AppActionTypes {
  GetAppInfo = '[App] Get app info',
  GetAppInfoSuccess = '[App] Get app info Success',
  GetAppInfoFailure = '[App] Get app info Failure',
}

export class GetAppInfo implements Action {
  readonly type = AppActionTypes.GetAppInfo;

  constructor(public payload: { appUrlName: string }) {
  }
}

export class GetAppInfoSuccess implements Action {
  readonly type = AppActionTypes.GetAppInfoSuccess;

  constructor(public payload: { data: PublicAppInfo }) {
  }
}

export class GetAppInfoFailure implements ErrorAction {
  readonly type = AppActionTypes.GetAppInfoFailure;

  constructor(public error: string) {
  }
}

export type AppActions = GetAppInfo | GetAppInfoSuccess | GetAppInfoFailure;

