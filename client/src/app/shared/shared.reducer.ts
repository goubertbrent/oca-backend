import { stateError, stateLoading, stateSuccess } from '@oca/web-shared';
import { onLoadableError, onLoadableLoad, onLoadableSuccess } from './loadable/loadable';
import { SharedActions, SharedActionTypes } from './shared.actions';
import { initialSharedState, SharedState } from './shared.state';

export function sharedReducer(state: SharedState = initialSharedState, action: SharedActions): SharedState {
  switch (action.type) {
    case SharedActionTypes.GET_BUDGET:
      return { ...state, budget: onLoadableLoad(initialSharedState.budget.data) };
    case SharedActionTypes.GET_BUDGET_COMPLETE:
      return { ...state, budget: onLoadableSuccess(action.payload) };
    case SharedActionTypes.GET_BUDGET_FAILED:
      return { ...state, budget: onLoadableError(action.error, initialSharedState.budget.data) };
    case SharedActionTypes.ADD_BUDGET:
      return { ...state, budget: onLoadableLoad(state.budget.data) };
    case SharedActionTypes.ADD_BUDGET_COMPLETE:
      return { ...state, budget: onLoadableSuccess(action.payload) };
    case SharedActionTypes.ADD_BUDGET_FAILED:
      return { ...state, budget: onLoadableError(action.error, state.budget.data) };
    case SharedActionTypes.GET_SOLUTION_SETTINGS:
      return { ...state, solutionSettings: onLoadableLoad(initialSharedState.solutionSettings.data) };
    case SharedActionTypes.GET_SOLUTION_SETTINGS_COMPLETE:
      return { ...state, solutionSettings: onLoadableSuccess(action.payload) };
    case SharedActionTypes.GET_SOLUTION_SETTINGS_FAILED:
      return { ...state, solutionSettings: onLoadableError(action.error, initialSharedState.solutionSettings.data) };
    case SharedActionTypes.GET_BRANDING_SETTINGS:
      return { ...state, brandingSettings: stateLoading(initialSharedState.brandingSettings.result) };
    case SharedActionTypes.GET_BRANDING_SETTINGS_COMPLETE:
      return { ...state, brandingSettings: stateSuccess(action.payload) };
    case SharedActionTypes.GET_BRANDING_SETTINGS_FAILED:
      return { ...state, brandingSettings: stateError(action.error, state.brandingSettings.result) };
    case SharedActionTypes.UPDATE_AVATAR:
    case SharedActionTypes.UPDATE_LOGO:
      return { ...state, brandingSettings: stateLoading(state.brandingSettings.result) };
    case SharedActionTypes.UPDATE_AVATAR_COMPLETE:
    case SharedActionTypes.UPDATE_LOGO_COMPLETE:
      return { ...state, brandingSettings: stateSuccess(action.payload) };
    case SharedActionTypes.UPDATE_AVATAR_FAILED:
    case SharedActionTypes.UPDATE_LOGO_FAILED:
      return { ...state, brandingSettings: stateError(action.error, state.brandingSettings.result) };
    case SharedActionTypes.GET_GLOBAL_CONFIG:
      if (state.globalConfig.result) {
        return state;
      }
      return { ...state, globalConfig: stateLoading(initialSharedState.globalConfig.result) };
    case SharedActionTypes.GET_GLOBAL_CONFIG_COMPLETE:
      return { ...state, globalConfig: stateSuccess(action.payload) };
    case SharedActionTypes.GET_COUNTRIES:
      return { ...state, countries: stateLoading(initialSharedState.countries.result) };
    case SharedActionTypes.GET_COUNTRIES_COMPLETE:
      return { ...state, countries: stateSuccess(action.payload) };
    case SharedActionTypes.GET_COUNTRIES_FAILED:
      return { ...state, countries: stateError(action.error, state.countries.result) };
    case SharedActionTypes.GET_AVAILABLE_PLACE_TYPES:
      return { ...state, availablePlaceTypes: stateLoading(initialSharedState.availablePlaceTypes.result) };
    case SharedActionTypes.GET_AVAILABLE_PLACE_TYPES_COMPLETE:
      return { ...state, availablePlaceTypes: stateSuccess(action.payload) };
    case SharedActionTypes.GET_AVAILABLE_PLACE_TYPES_FAILED:
      return { ...state, availablePlaceTypes: stateError(action.error, state.availablePlaceTypes.result) };
  }
  return state;
}
