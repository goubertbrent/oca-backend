import { Action } from '@ngrx/store';
import { AppMerchant, AppMerchantList, City, Project, ProjectDetails, UserSettings } from './projects';

export const enum ProjectsActionTypes {
  GET_CITY = '[projects] Get city',
  GET_CITY_COMPLETE = '[projects] city complete',
  GET_CITY_FAILED = '[projects] city failed',
  GET_PROJECT_DETAILS = '[projects] Get project details',
  GET_PROJECT_DETAILS_COMPLETE = '[projects] Get project details complete',
  GET_PROJECT_DETAILS_FAILED = '[projects] Get project details failed',
  GET_PROJECTS = '[projects] Get projects',
  GET_PROJECTS_COMPLETE = '[projects] Get projects complete',
  GET_PROJECTS_FAILED = '[projects] Get projects failed',
  ADD_PARTICIPATION = '[projects] Add participation',
  ADD_PARTICIPATION_COMPLETE = '[projects] Add participation complete',
  ADD_PARTICIPATION_FAILED = '[projects] Add participation failed',
  GET_MERCHANT = '[projects] Get merchant',
  GET_MERCHANT_COMPLETE = '[projects] Get merchant complete',
  GET_MERCHANT_FAILED = '[projects] Get merchant failed',
  GET_MERCHANTS = '[projects] Get merchants',
  GET_MERCHANTS_COMPLETE = '[projects] Get merchants complete',
  GET_MERCHANTS_FAILED = '[projects] Get merchants failed',
  GET_MORE_MERCHANTS = '[projects] Get more merchants',
  GET_MORE_MERCHANTS_COMPLETE = '[projects] Get more merchants complete',
  GET_MORE_MERCHANTS_FAILED = '[projects] Get more merchants failed',
  SHOW_DIALOG = '[projects] Show dialog',
  DISMISS_DIALOG = '[projects] Dismiss dialog',
  GET_USER_SETTINGS = '[projects] Get user settings',
  GET_USER_SETTINGS_COMPLETE = '[projects] Get user settings complete',
  GET_USER_SETTINGS_FAILED = '[projects] Get user settings failed',
  SAVE_USER_SETTINGS = '[projects] Save user settings',
  SAVE_USER_SETTINGS_COMPLETE = '[projects] Save user settings complete',
  SAVE_USER_SETTINGS_FAILED = '[projects] Save user settings failed',
}

export class GetCityAction implements Action {
  readonly type = ProjectsActionTypes.GET_CITY;

  constructor(public payload: { id: string }) {
  }
}

export class GetCityCompleteAction implements Action {
  readonly type = ProjectsActionTypes.GET_CITY_COMPLETE;

  constructor(public payload: City) {
  }
}

export class GetCityFailedAction implements Action {
  readonly type = ProjectsActionTypes.GET_CITY_FAILED;

  constructor(public error: string) {
  }
}

export class GetProjectDetailsAction implements Action {
  readonly type = ProjectsActionTypes.GET_PROJECT_DETAILS;

  constructor(public payload: { id: number }) {
  }
}

export class GetProjectDetailsCompleteAction implements Action {
  readonly type = ProjectsActionTypes.GET_PROJECT_DETAILS_COMPLETE;

  constructor(public payload: ProjectDetails) {
  }
}

export class GetProjectDetailsFailedAction implements Action {
  readonly type = ProjectsActionTypes.GET_PROJECT_DETAILS_FAILED;

  constructor(public error: string) {
  }
}

export class GetProjectsAction implements Action {
  readonly type = ProjectsActionTypes.GET_PROJECTS;
}

export class GetProjectsCompleteAction implements Action {
  readonly type = ProjectsActionTypes.GET_PROJECTS_COMPLETE;

  constructor(public payload: Project[]) {
  }
}

export class GetProjectsFailedAction implements Action {
  readonly type = ProjectsActionTypes.GET_PROJECTS_FAILED;

  constructor(public error: string) {
  }
}

export class AddParticipationAction implements Action {
  readonly type = ProjectsActionTypes.ADD_PARTICIPATION;

  constructor(public payload: { projectId: number, qrContent: string }) {
  }
}

export class AddParticipationCompleteAction implements Action {
  readonly type = ProjectsActionTypes.ADD_PARTICIPATION_COMPLETE;

  constructor(public payload: ProjectDetails) {
  }
}

export class AddParticipationFailedAction implements Action {
  readonly type = ProjectsActionTypes.ADD_PARTICIPATION_FAILED;

  constructor(public error: string) {
  }
}

export class GetMerchantAction implements Action {
  readonly type = ProjectsActionTypes.GET_MERCHANT;

  constructor(public payload: { id: number }) {
  }
}

export class GetMerchantCompleteAction implements Action {
  readonly type = ProjectsActionTypes.GET_MERCHANT_COMPLETE;

  constructor(public payload: AppMerchant) {
  }
}

export class GetMerchantFailedAction implements Action {
  readonly type = ProjectsActionTypes.GET_MERCHANT_FAILED;

  constructor(public error: string) {
  }
}

export class GetMerchantsAction implements Action {
  readonly type = ProjectsActionTypes.GET_MERCHANTS;
}

export class GetMerchantsCompleteAction implements Action {
  readonly type = ProjectsActionTypes.GET_MERCHANTS_COMPLETE;

  constructor(public payload: AppMerchantList) {
  }
}

export class GetMerchantsFailedAction implements Action {
  readonly type = ProjectsActionTypes.GET_MERCHANTS_FAILED;

  constructor(public error: string) {
  }
}

export class GetMoreMerchantsAction implements Action {
  readonly type = ProjectsActionTypes.GET_MORE_MERCHANTS;
}

export class GetMoreMerchantsCompleteAction implements Action {
  readonly type = ProjectsActionTypes.GET_MORE_MERCHANTS_COMPLETE;

  constructor(public payload: AppMerchantList) {
  }
}

export class GetMoreMerchantsFailedAction implements Action {
  readonly type = ProjectsActionTypes.GET_MORE_MERCHANTS_FAILED;

  constructor(public error: string) {
  }
}

export class GetUserSettingsAction implements Action {
  readonly type = ProjectsActionTypes.GET_USER_SETTINGS;
}

export class GetUserSettingsCompleteAction implements Action {
  readonly type = ProjectsActionTypes.GET_USER_SETTINGS_COMPLETE;

  constructor(public payload: UserSettings) {
  }
}

export class GetUserSettingsFailedAction implements Action {
  readonly type = ProjectsActionTypes.GET_USER_SETTINGS_FAILED;

  constructor(public error: string) {
  }
}

export class SaveUserSettingsAction implements Action {
  readonly type = ProjectsActionTypes.SAVE_USER_SETTINGS;

  constructor(public payload: UserSettings) {
  }
}

export class SaveUserSettingsCompleteAction implements Action {
  readonly type = ProjectsActionTypes.SAVE_USER_SETTINGS_COMPLETE;

  constructor(public payload: UserSettings) {
  }
}

export class SaveUserSettingsFailedAction implements Action {
  readonly type = ProjectsActionTypes.SAVE_USER_SETTINGS_FAILED;

  constructor(public error: string) {
  }
}

export type ProjectsActions = GetCityAction
  | GetCityCompleteAction
  | GetCityFailedAction
  | GetProjectDetailsAction
  | GetProjectDetailsCompleteAction
  | GetProjectDetailsFailedAction
  | GetProjectsAction
  | GetProjectsCompleteAction
  | GetProjectsFailedAction
  | AddParticipationAction
  | AddParticipationCompleteAction
  | AddParticipationFailedAction
  | GetMerchantAction
  | GetMerchantCompleteAction
  | GetMerchantFailedAction
  | GetMerchantsAction
  | GetMerchantsCompleteAction
  | GetMerchantsFailedAction
  | GetMoreMerchantsAction
  | GetMoreMerchantsCompleteAction
  | GetMoreMerchantsFailedAction
  | GetUserSettingsAction
  | GetUserSettingsCompleteAction
  | GetUserSettingsFailedAction
  | SaveUserSettingsAction
  | SaveUserSettingsCompleteAction
  | SaveUserSettingsFailedAction;

