import { stateError, stateLoading, stateSuccess } from '@oca/shared';
import { updateItem } from '../util';
import { ProjectsActions, ProjectsActionTypes } from './projects.actions';
import { initialProjectsState, ProjectsState } from './projects.state';

export function projectsReducer(state = initialProjectsState, action: ProjectsActions): ProjectsState {
  switch (action.type) {
    case ProjectsActionTypes.GET_CITY:
      return {
        ...state,
        city: stateLoading(initialProjectsState.city.result),
      };
    case ProjectsActionTypes.GET_CITY_COMPLETE:
      return { ...state, city: stateSuccess(action.payload) };
    case ProjectsActionTypes.GET_CITY_FAILED:
      return { ...state, city: stateError(action.error, initialProjectsState.city.result) };
    case ProjectsActionTypes.GET_PROJECT_DETAILS:
      return {
        ...state,
        currentProjectId: action.payload.id,
        projectDetails: stateLoading(initialProjectsState.projectDetails.result),
      };
    case ProjectsActionTypes.GET_PROJECT_DETAILS_COMPLETE:
      return {
        ...state,
        projectDetails: stateSuccess(action.payload),
      };
    case ProjectsActionTypes.GET_PROJECT_DETAILS_FAILED:
      return {
        ...state,
        projectDetails: stateError(action.error, initialProjectsState.projectDetails.result),
      };
    case ProjectsActionTypes.GET_PROJECTS:
      return { ...state, projects: stateLoading(state.projects.result) };
    case ProjectsActionTypes.GET_PROJECTS_COMPLETE:
      return { ...state, projects: stateSuccess(action.payload) };
    case ProjectsActionTypes.GET_PROJECTS_FAILED:
      return { ...state, projects: stateError(action.error, state.projects.result) };
    case ProjectsActionTypes.GET_MERCHANT:
      return { ...state, merchantDetails: stateLoading(initialProjectsState.merchantDetails.result) };
    case ProjectsActionTypes.GET_MERCHANT_COMPLETE:
      return { ...state, merchantDetails: stateSuccess(action.payload) };
    case ProjectsActionTypes.GET_MERCHANT_FAILED:
      return { ...state, merchantDetails: stateError(action.error, state.merchantDetails.result) };
    case ProjectsActionTypes.GET_MERCHANTS:
      return { ...state, merchants: stateLoading(initialProjectsState.merchants.result) };
    case ProjectsActionTypes.GET_MERCHANTS_COMPLETE:
      return { ...state, merchants: stateSuccess(action.payload) };
    case ProjectsActionTypes.GET_MERCHANTS_FAILED:
      return { ...state, merchants: stateError(action.error, state.merchants.result) };
    case ProjectsActionTypes.GET_MORE_MERCHANTS:
      return { ...state, merchants: stateLoading(state.merchants.result) };
    case ProjectsActionTypes.GET_MORE_MERCHANTS_COMPLETE:
      return {
        ...state,
        merchants: stateSuccess({
          ...action.payload,
          results: [ ...(state.merchants.result ? state.merchants.result.results : []), ...action.payload.results ],
        }),
      };
    case ProjectsActionTypes.GET_MORE_MERCHANTS_FAILED:
      return { ...state, merchants: stateError(action.error, state.merchants.result) };
    case ProjectsActionTypes.ADD_PARTICIPATION_COMPLETE:
      return {
        ...state,
        currentProjectId: action.payload.id,
        projects: stateSuccess(updateItem(state.projects.result ?? [], action.payload, 'id')),
        projectDetails: stateSuccess(action.payload),
      };
    case ProjectsActionTypes.GET_USER_SETTINGS:
      return { ...state, userSettings: stateLoading(initialProjectsState.userSettings.result) };
    case ProjectsActionTypes.GET_USER_SETTINGS_COMPLETE:
      return { ...state, userSettings: stateSuccess(action.payload) };
    case ProjectsActionTypes.GET_USER_SETTINGS_FAILED:
      return { ...state, userSettings: stateError(action.error, initialProjectsState.userSettings.result) };
    case ProjectsActionTypes.SAVE_USER_SETTINGS:
      return { ...state, userSettings: stateLoading(action.payload) };
    case ProjectsActionTypes.SAVE_USER_SETTINGS_COMPLETE:
      return { ...state, userSettings: stateSuccess(action.payload) };
    case ProjectsActionTypes.SAVE_USER_SETTINGS_FAILED:
      return { ...state, userSettings: stateError(action.error, initialProjectsState.userSettings.result) };
  }
  return state;
}
