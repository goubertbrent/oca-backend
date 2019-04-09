import { HttpErrorResponse } from '@angular/common/http';
import { Action } from '@ngrx/store';
import { ServiceMenuDetail } from './rogerthat';

export const enum SharedActionTypes {
  GET_MENU = '[shared] Get menu',
  GET_MENU_COMPLETE = '[forms] Get menu complete',
  GET_MENU_FAILED = '[forms] Get menu failed',
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

export type SharedActions = GetMenuAction | GetMenuCompleteAction | GetMenuFailedAction;
