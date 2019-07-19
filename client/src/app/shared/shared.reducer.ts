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
      return { ...state, serviceMenu: onLoadableError(action.error, initialSharedState.serviceMenu.data) };
    case SharedActionTypes.GET_INFO:
      return { ...state, serviceIdentityInfo: onLoadableLoad(initialSharedState.serviceIdentityInfo.data) };
    case SharedActionTypes.GET_INFO_COMPLETE:
      return { ...state, serviceIdentityInfo: onLoadableSuccess(action.payload) };
    case SharedActionTypes.GET_INFO_FAILED:
      return { ...state, serviceIdentityInfo: onLoadableError(action.error, initialSharedState.serviceIdentityInfo.data) };
    case SharedActionTypes.GET_APPS:
      return { ...state, apps: onLoadableLoad(initialSharedState.apps.data) };
    case SharedActionTypes.GET_APPS_COMPLETE:
      return { ...state, apps: onLoadableSuccess(action.payload) };
    case SharedActionTypes.GET_APPS_FAILED:
      return { ...state, apps: onLoadableError(action.error, initialSharedState.apps.data) };
    case SharedActionTypes.GET_APP_STATISTICS:
      return { ...state, appStatistics: onLoadableLoad(initialSharedState.appStatistics.data) };
    case SharedActionTypes.GET_APP_STATISTICS_COMPLETE:
      return { ...state, appStatistics: onLoadableSuccess(action.payload) };
    case SharedActionTypes.GET_APP_STATISTICS_FAILED:
      return { ...state, appStatistics: onLoadableError(action.error, initialSharedState.appStatistics.data) };
    case SharedActionTypes.GET_BUDGET:
      return { ...state, budget: onLoadableLoad(initialSharedState.budget.data) };
    case SharedActionTypes.GET_BUDGET_COMPLETE:
      return { ...state, budget: onLoadableSuccess(action.payload) };
    case SharedActionTypes.GET_BUDGET_FAILED:
      return { ...state, budget: onLoadableError(action.error, initialSharedState.budget.data) };
    case SharedActionTypes.GET_SOLUTION_SETTINGS:
      return { ...state, solutionSettings: onLoadableLoad(initialSharedState.solutionSettings.data) };
    case SharedActionTypes.GET_SOLUTION_SETTINGS_COMPLETE:
      return { ...state, solutionSettings: onLoadableSuccess(action.payload) };
    case SharedActionTypes.GET_SOLUTION_SETTINGS_FAILED:
      return { ...state, solutionSettings: onLoadableError(action.error, initialSharedState.solutionSettings.data) };
    case SharedActionTypes.GET_BRANDING_SETTINGS:
      return { ...state, brandingSettings: onLoadableLoad(initialSharedState.brandingSettings.data) };
    case SharedActionTypes.GET_BRANDING_SETTINGS_COMPLETE:
      return { ...state, brandingSettings: onLoadableSuccess(action.payload) };
    case SharedActionTypes.GET_BRANDING_SETTINGS_FAILED:
      return { ...state, brandingSettings: onLoadableError(action.error, initialSharedState.brandingSettings.data) };
  }
  return state;
}