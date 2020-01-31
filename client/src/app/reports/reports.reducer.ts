import { EMPTY_ARRAY, stateError, stateLoading, stateSuccess } from '../shared/util';
import { ReportsActions, ReportsActionTypes } from './reports.actions';
import { initialState, ReportsState } from './reports.state';

export function reportsReducer(state: ReportsState = initialState, action: ReportsActions): ReportsState {
  switch (action.type) {
    case ReportsActionTypes.GET_INCIDENTS:
      // no cursor => reset
      return { ...state, incidents: stateLoading(action.payload.cursor ? state.incidents.result : initialState.incidents.result) };
    case ReportsActionTypes.GET_INCIDENTS_COMPLETE:
      return {
        ...state,
        incidents: stateSuccess({
          ...action.payload,
          results: [...(state.incidents.result ? state.incidents.result.results : []), ...action.payload.results],
        }),
      };
    case ReportsActionTypes.GET_INCIDENTS_FAILED:
      return { ...state, incidents: stateError(action.error, state.incidents.result) };
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
    case ReportsActionTypes.LIST_INCIDENT_STATISTICS:
      return {
        ...state, statisticsList: stateLoading(initialState.statisticsList.result),
        statistics: initialState.statistics,
      };
    case ReportsActionTypes.LIST_INCIDENT_STATISTICS_COMPLETE:
      return { ...state, statisticsList: stateSuccess(action.payload) };
    case ReportsActionTypes.LIST_INCIDENT_STATISTICS_FAILED:
      return { ...state, statisticsList: stateError(action.error, state.statisticsList.result) };
    case ReportsActionTypes.GET_INCIDENT_STATISTICS:
      return { ...state, statistics: stateLoading(state.statistics.result) };
    case ReportsActionTypes.GET_INCIDENT_STATISTICS_COMPLETE:
      // This list only ever grows
      return { ...state, statistics: stateSuccess([...(state.statistics.result || EMPTY_ARRAY), ...action.payload]) };
    case ReportsActionTypes.GET_INCIDENT_STATISTICS_FAILED:
      return { ...state, statistics: stateError(action.error, state.statistics.result) };
    case ReportsActionTypes.SET_INCIDENT_STATS_FILTER:
      return { ...state, statisticsFilter: action.payload };
  }
  return state;
}
