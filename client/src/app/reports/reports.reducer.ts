import { stateError, stateLoading, stateSuccess } from '../shared/util';
import { ReportsActions, ReportsActionTypes } from './reports.actions';
import { initialState, ReportsState } from './reports.state';

export function reportsReducer(state: ReportsState = initialState, action: ReportsActions): ReportsState {
  switch (action.type) {
    case ReportsActionTypes.GET_INCIDENTS:
      // no cursor => reset
      return { ...state, incidents: action.payload.cursor ? state.incidents : initialState.incidents };
    case ReportsActionTypes.GET_INCIDENTS_COMPLETE:
      return { ...state, incidents: { ...action.payload, results: [...state.incidents.results, ...action.payload.results] } };
    case ReportsActionTypes.GET_MAP_CONFIG:
      return { ...state, mapConfig: stateLoading(initialState.mapConfig.result) };
    case ReportsActionTypes.GET_MAP_CONFIG_COMPLETE:
      return { ...state, mapConfig: stateSuccess(action.payload) };
    case ReportsActionTypes.GET_MAP_CONFIG_FAILED:
      return { ...state, mapConfig: stateError(action.error, state.mapConfig.result) };
    case ReportsActionTypes.SAVE_MAP_CONFIG:
      return { ...state, mapConfig: stateLoading(action.payload) };
    case ReportsActionTypes.SAVE_MAP_CONFIG_COMPLETE:
      return { ...state, mapConfig: stateSuccess(action.payload) };
    case ReportsActionTypes.SAVE_MAP_CONFIG_FAILED:
      return { ...state, mapConfig: stateError(action.error, state.mapConfig.result) };
    case ReportsActionTypes.GET_INCIDENT:
      return { ...state, incident: stateLoading(initialState.incident.result) };
    case ReportsActionTypes.GET_INCIDENT_COMPLETE:
      return { ...state, incident: stateSuccess(action.payload) };
    case ReportsActionTypes.GET_INCIDENT_FAILED:
      return { ...state, incident: stateError(action.error, state.incident.result) };
    case ReportsActionTypes.UPDATE_INCIDENT:
      return { ...state, incident: stateLoading(action.payload) };
    case ReportsActionTypes.UPDATE_INCIDENT_COMPLETE:
      return { ...state, incident: stateSuccess(action.payload) };
    case ReportsActionTypes.UPDATE_INCIDENT_FAILED:
      return { ...state, incident: stateError(action.error, state.incident.result) };
  }
  return state;
}
