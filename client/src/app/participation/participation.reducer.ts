import { onLoadableError, onLoadableLoad, onLoadableSuccess } from '../shared/loadable/loadable';
import { ParticipationActions, ParticipationActionTypes } from './participation.actions';
import { initialState, ParticipationState } from './participation.state';

export function participationReducer(state: ParticipationState = initialState, action: ParticipationActions): ParticipationState {
  switch (action.type) {
    case ParticipationActionTypes.GET_PROJECTS:
      return { ...state, projects: onLoadableLoad(initialState.projects.data) };
    case ParticipationActionTypes.GET_PROJECTS_COMPLETE:
      return { ...state, projects: onLoadableSuccess(action.payload) };
    case ParticipationActionTypes.GET_PROJECTS_FAILED:
      return { ...state, projects: onLoadableError(action.error, state.projects.data) };
    case ParticipationActionTypes.GET_PROJECT:
      return { ...state, projectDetails: onLoadableLoad(initialState.projectDetails.data) };
    case ParticipationActionTypes.GET_PROJECT_COMPLETE:
      return { ...state, projectDetails: onLoadableSuccess(action.payload) };
    case ParticipationActionTypes.GET_PROJECT_FAILED:
      return { ...state, projectDetails: onLoadableError(action.error, state.projectDetails.data) };
    case ParticipationActionTypes.SAVE_PROJECT:
      return { ...state, projectDetails: onLoadableLoad(state.projectDetails.data) };
    case ParticipationActionTypes.SAVE_PROJECT_COMPLETE:
      return { ...state, projectDetails: onLoadableSuccess(action.payload) };
    case ParticipationActionTypes.SAVE_PROJECT_FAILED:
      return { ...state, projectDetails: onLoadableError(action.error, state.projectDetails.data) };
    case ParticipationActionTypes.CREATE_PROJECT:
      return { ...state, projectDetails: onLoadableLoad(state.projectDetails.data) };
    case ParticipationActionTypes.CREATE_PROJECT_COMPLETE:
      return { ...state, projectDetails: onLoadableSuccess(action.payload) };
    case ParticipationActionTypes.CREATE_PROJECT_FAILED:
      return { ...state, projectDetails: onLoadableError(action.error, state.projectDetails.data) };
    case ParticipationActionTypes.GET_PROJECT_STATISTICS:
      return { ...state, projectStatistics: onLoadableLoad(initialState.projectStatistics.data) };
    case ParticipationActionTypes.GET_PROJECT_STATISTICS_COMPLETE:
      return {
        ...state,
        projectStatistics: onLoadableSuccess({
          ...state,
          ...action.payload,
          results: state.projectStatistics.data ?
            [ ...state.projectStatistics.data.results, ...action.payload.results ] : action.payload.results,
        }),
      };
    case ParticipationActionTypes.GET_PROJECT_STATISTICS_FAILED:
      return { ...state, projectStatistics: onLoadableError(action.error, state.projectStatistics.data) };
    case ParticipationActionTypes.GET_SETTINGS:
      return { ...state, settings: onLoadableLoad(initialState.settings.data) };
    case ParticipationActionTypes.GET_SETTINGS_COMPLETE:
      return { ...state, settings: onLoadableSuccess(action.payload) };
    case ParticipationActionTypes.GET_SETTINGS_FAILED:
      return { ...state, settings: onLoadableError(action.error, state.settings.data) };
    case ParticipationActionTypes.UPDATE_SETTINGS:
      return { ...state, settings: onLoadableLoad(state.settings.data) };
    case ParticipationActionTypes.UPDATE_SETTINGS_COMPLETE:
      return { ...state, settings: onLoadableSuccess(action.payload) };
    case ParticipationActionTypes.UPDATE_SETTINGS_FAILED:
      return { ...state, settings: onLoadableError(action.error, state.settings.data) };
  }
  return state;
}
