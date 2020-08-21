import { SidebarActions, SidebarActionTypes } from '../actions';
import { initialSidebarState, ISidebarState } from '../states';

export function sidebarReducer(state: ISidebarState = initialSidebarState, action: SidebarActions): ISidebarState {
  switch (action.type) {
    case SidebarActionTypes.UPDATE_SIDEBAR_ITEMS:
      return {
        ...state,
        sidebarItems: action.payload,
      };
    case SidebarActionTypes.ADD_ROUTES:
      return {
        ...state,
        routes: [...state.routes, ...action.payload],
      };
  }
  return state;
}
