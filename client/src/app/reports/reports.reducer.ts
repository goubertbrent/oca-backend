import { stateError, stateLoading, stateSuccess } from '@oca/web-shared';
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
