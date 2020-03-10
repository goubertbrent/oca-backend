import { stateError, stateLoading, stateSuccess } from '../shared/util';
import { SettingsActions, SettingsActionTypes } from './settings.actions';
import { initialSettingsState, SettingsState } from './settings.state';

export function settingsReducer(state: SettingsState = initialSettingsState, action: SettingsActions): SettingsState {
  switch (action.type) {
    case SettingsActionTypes.GET_OPENING_HOURS:
      return { ...state, openingHours: stateLoading(initialSettingsState.openingHours.result) };
    case SettingsActionTypes.GET_OPENING_HOURS_COMPLETE:
      return { ...state, openingHours: stateSuccess(action.payload) };
    case SettingsActionTypes.GET_OPENING_HOURS_FAILED:
      return { ...state, openingHours: stateError(action.error, initialSettingsState.openingHours.result) };
    case SettingsActionTypes.SAVE_OPENING_HOURS:
      return { ...state, openingHours: stateLoading(action.payload) };
    case SettingsActionTypes.SAVE_OPENING_HOURS_COMPLETE:
      return { ...state, openingHours: stateSuccess(action.payload) };
    case SettingsActionTypes.SAVE_OPENING_HOURS_FAILED:
      return { ...state, openingHours: stateError(action.error, state.openingHours.result) };
    case SettingsActionTypes.GET_SERVICE_INFO:
      return { ...state, serviceInfo: stateLoading(initialSettingsState.serviceInfo.result) };
    case SettingsActionTypes.GET_SERVICE_INFO_COMPLETE:
      return { ...state, serviceInfo: stateSuccess(action.payload) };
    case SettingsActionTypes.GET_SERVICE_INFO_FAILED:
      return { ...state, serviceInfo: stateError(action.error, state.serviceInfo.result) };
    case SettingsActionTypes.UPDATE_SERVICE_INFO:
      return { ...state, serviceInfo: stateLoading(action.payload) };
    case SettingsActionTypes.UPDATE_SERVICE_INFO_COMPLETE:
      return { ...state, serviceInfo: stateSuccess(action.payload) };
    case SettingsActionTypes.UPDATE_SERVICE_INFO_FAILED:
      return { ...state, serviceInfo: stateError(action.error, state.serviceInfo.result) };
    case SettingsActionTypes.GET_AVAILABLE_PLACE_TYPES:
      return { ...state, availablePlaceTypes: stateLoading(initialSettingsState.availablePlaceTypes.result) };
    case SettingsActionTypes.GET_AVAILABLE_PLACE_TYPES_COMPLETE:
      return { ...state, availablePlaceTypes: stateSuccess(action.payload) };
    case SettingsActionTypes.GET_AVAILABLE_PLACE_TYPES_FAILED:
      return { ...state, availablePlaceTypes: stateError(action.error, state.availablePlaceTypes.result) };
  }
  return state;
}
