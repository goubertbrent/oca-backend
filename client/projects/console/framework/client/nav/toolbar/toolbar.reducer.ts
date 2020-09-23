import { insertItem, removeItem, updateItem } from '../../../../src/app/ngrx';
import { ToolbarActions, ToolbarActionTypes } from './toolbar.action';
import { initialToolbarState, IToolbarState } from './toolbar.state';

export function toolbarReducer(state: IToolbarState = initialToolbarState, action: ToolbarActions): IToolbarState {
  switch (action.type) {
    case ToolbarActionTypes.ADD_ITEM:
      return {
        ...state,
        items: insertItem(state.items.filter(i => i.id !== action.payload.id), action.payload),
      };
    case ToolbarActionTypes.UPDATE_ITEM:
      return {
        ...state,
        items: updateItem(state.items, action.payload, 'id'),
      };
    case ToolbarActionTypes.REMOVE_ITEM:
      return {
        ...state,
        items: removeItem(state.items, action.payload, 'id'),
      };
    case ToolbarActionTypes.CLEAN_ITEMS:
      return {
        ...state,
        items: [...state.items.filter(item => item.persistent)],
      };
    case ToolbarActionTypes.CLEAR_ITEMS:
      return {
        ...state,
        items: [],
      };
  }
  return state;
}
