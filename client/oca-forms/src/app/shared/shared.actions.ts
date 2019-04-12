import { HttpErrorResponse } from '@angular/common/http';
import { Action } from '@ngrx/store';
import { Budget } from './billing/billing';
import { AppStatistics, ServiceIdentityInfo, ServiceMenuDetail } from './rogerthat';

export const enum SharedActionTypes {
  GET_MENU = '[shared] Get menu',
  GET_MENU_COMPLETE = '[shared] Get menu complete',
  GET_MENU_FAILED = '[shared] Get menu failed',
  GET_SERVICE_IDENTITY = '[shared] Get service identity',
  GET_SERVICE_IDENTITY_COMPLETE = '[shared] Get service identity complete',
  GET_SERVICE_IDENTITY_FAILED = '[shared] Get service identity failed',
  GET_APP_STATISTICS = '[shared] Get app statistics',
  GET_APP_STATISTICS_COMPLETE = '[shared] Get app statistics complete',
  GET_APP_STATISTICS_FAILED = '[shared] Get app statistics failed',
  GET_BUDGET = '[shared] Get budget',
  GET_BUDGET_COMPLETE = '[shared] Get budget complete',
  GET_BUDGET_FAILED = '[shared] Get budget failed',
}

export class GetMenuAction implements Action {
  readonly type = SharedActionTypes.GET_MENU;
}

export class GetMenuCompleteAction implements Action {
  readonly type = SharedActionTypes.GET_MENU_COMPLETE;

  constructor(public payload: ServiceMenuDetail) {
  }
}

export class GetMenuFailedAction implements Action {
  readonly type = SharedActionTypes.GET_MENU_FAILED;

  constructor(public payload: HttpErrorResponse) {
  }
}

export class GetServiceIdentityAction implements Action {
  readonly type = SharedActionTypes.GET_SERVICE_IDENTITY;
}

export class GetServiceIdentityCompleteAction implements Action {
  readonly type = SharedActionTypes.GET_SERVICE_IDENTITY_COMPLETE;

  constructor(public payload: ServiceIdentityInfo) {
  }
}

export class GetServiceIdentityFailedAction implements Action {
  readonly type = SharedActionTypes.GET_SERVICE_IDENTITY_FAILED;

  constructor(public payload: HttpErrorResponse) {
  }
}

export class GetAppStatisticsAction implements Action {
  readonly type = SharedActionTypes.GET_APP_STATISTICS;
}

export class GetAppStatisticsCompleteAction implements Action {
  readonly type = SharedActionTypes.GET_APP_STATISTICS_COMPLETE;

  constructor(public payload: AppStatistics[]) {
  }
}

export class GetAppStatisticsFailedAction implements Action {
  readonly type = SharedActionTypes.GET_APP_STATISTICS_FAILED;

  constructor(public payload: HttpErrorResponse) {
  }
}
export class GetBudgetAction implements Action {
  readonly type = SharedActionTypes.GET_BUDGET;
}

export class GetBudgetCompleteAction implements Action {
  readonly type = SharedActionTypes.GET_BUDGET_COMPLETE;

  constructor(public payload: Budget) {
  }
}

export class GetBudgetFailedAction implements Action {
  readonly type = SharedActionTypes.GET_BUDGET_FAILED;

  constructor(public payload: HttpErrorResponse) {
  }
}

export type SharedActions =
  GetMenuAction
  | GetMenuCompleteAction
  | GetMenuFailedAction
  | GetServiceIdentityAction
  | GetServiceIdentityCompleteAction
  | GetServiceIdentityFailedAction
  | GetAppStatisticsAction
  | GetAppStatisticsCompleteAction
  | GetAppStatisticsFailedAction
  | GetBudgetAction
  | GetBudgetCompleteAction
  | GetBudgetFailedAction;
