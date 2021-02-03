import { stateLoading, stateSuccess, stateError } from '@oca/web-shared';
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
  }
  return state;
}
