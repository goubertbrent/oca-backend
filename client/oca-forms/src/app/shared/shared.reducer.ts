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
    case SharedActionTypes.GET_SERVICE_IDENTITY:
      return { ...state, serviceInfo: onLoadableLoad(initialSharedState.serviceInfo.data) };
    case SharedActionTypes.GET_SERVICE_IDENTITY_COMPLETE:
      return { ...state, serviceInfo: onLoadableSuccess(action.payload) };
    case SharedActionTypes.GET_SERVICE_IDENTITY_FAILED:
      return { ...state, serviceInfo: onLoadableError(action.payload) };
    case SharedActionTypes.GET_APP_STATISTICS:
      return { ...state, appStatistics: onLoadableLoad(initialSharedState.appStatistics.data) };
    case SharedActionTypes.GET_APP_STATISTICS_COMPLETE:
      return { ...state, appStatistics: onLoadableSuccess(action.payload) };
    case SharedActionTypes.GET_APP_STATISTICS_FAILED:
      return { ...state, appStatistics: onLoadableError(action.payload) };
    case SharedActionTypes.GET_BUDGET:
      return { ...state, budget: onLoadableLoad(initialSharedState.budget.data) };
    case SharedActionTypes.GET_BUDGET_COMPLETE:
      return { ...state, budget: onLoadableSuccess(action.payload) };
    case SharedActionTypes.GET_BUDGET_FAILED:
      return { ...state, budget: onLoadableError(action.payload) };
  }
  return state;
}
