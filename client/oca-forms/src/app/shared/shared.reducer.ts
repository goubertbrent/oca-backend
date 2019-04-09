import { onLoadableError, onLoadableLoad, onLoadableSuccess } from './loadable/loadable';
import { SharedActions, SharedActionTypes } from './shared.actions';
import { initialSharedState, SharedState } from './shared.state';

export function sharedReducer(state: SharedState = initialSharedState, action: SharedActions): SharedState {
  switch (action.type) {
    case SharedActionTypes.GET_MENU:
      return { ...state, serviceMenu: onLoadableLoad(initialSharedState.serviceMenu.data) };
    case SharedActionTypes.GET_MENU_COMPLETE:
      return { ...state, serviceMenu: onLoadableSuccess(action.payload) };
    case SharedActionTypes.GET_MENU_FAILED:
      return { ...state, serviceMenu: onLoadableError(action.payload) };
  }
  return state;
}
