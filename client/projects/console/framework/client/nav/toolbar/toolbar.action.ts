import { Action } from '@ngrx/store';
import { ToolbarItem } from './toolbar.interfaces';

export const enum ToolbarActionTypes {
  ADD_ITEM = '[Toolbar] Add Item',
  UPDATE_ITEM = '[Toolbar] Update Item',
  REMOVE_ITEM = '[Toolbar] Remove Item',
  CLEAN_ITEMS = '[Toolbar] Clean Non-persistent Items',
  SET_ITEMS = '[Toolbar] Set items',
  CLEAR_ITEMS = '[Toolbar] Clear items',
}

export class AddToolbarItemAction implements Action {
  readonly type = ToolbarActionTypes.ADD_ITEM;

  constructor(public payload: ToolbarItem) {
  }
}

export class UpdateToolbarItemAction implements Action {
  readonly type = ToolbarActionTypes.UPDATE_ITEM;

  constructor(public payload: ToolbarItem) {
  }
}

export class RemoveToolbarItemAction implements Action {
  readonly type = ToolbarActionTypes.REMOVE_ITEM;

  constructor(public payload: string /* item id */) {
  }
}

export class CleanToolbarItemsAction implements Action {
  readonly type = ToolbarActionTypes.CLEAN_ITEMS;
}

export class ClearToolbarItemsAction implements Action {
  readonly type = ToolbarActionTypes.CLEAR_ITEMS;
}

export type ToolbarActions
  = AddToolbarItemAction
  | UpdateToolbarItemAction
  | RemoveToolbarItemAction
  | CleanToolbarItemsAction
  | ClearToolbarItemsAction;
