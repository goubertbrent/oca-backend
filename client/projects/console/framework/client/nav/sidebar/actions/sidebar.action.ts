import { Action } from '@ngrx/store';
import { Route } from '../../../../../src/app/app.routes';
import { SidebarItem } from '../interfaces';

export const enum SidebarActionTypes {
  ADD_ROUTES = '[Sidebar] Add routes',
  UPDATE_SIDEBAR_ITEMS = '[Sidebar] Update items',
}

export class AddRoutesAction implements Action {
  readonly type = SidebarActionTypes.ADD_ROUTES;

  constructor(public payload: Route[]) {
  }
}

export class UpdateSidebarItemsAction implements Action {
  readonly type = SidebarActionTypes.UPDATE_SIDEBAR_ITEMS;

  constructor(public payload: SidebarItem[]) {
  }
}

export type SidebarActions
  = AddRoutesAction
  | UpdateSidebarItemsAction;
