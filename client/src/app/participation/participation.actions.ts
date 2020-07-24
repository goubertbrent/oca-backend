import { Action } from '@ngrx/store';
import { ApiError } from '@oca/web-shared';
import { CitySettings, CreateProject, Project, ProjectStatistics } from './projects';

export const enum ParticipationActionTypes {
  GET_PROJECTS = '[psp] Get projects',
  GET_PROJECTS_COMPLETE = '[psp] Get projects complete',
  GET_PROJECTS_FAILED = '[psp] Get projects failed',
  GET_PROJECT = '[psp] Get project',
  GET_PROJECT_COMPLETE = '[psp] Get project complete',
  GET_PROJECT_FAILED = '[psp] Get project failed',
  SAVE_PROJECT = '[psp] Save project',
  SAVE_PROJECT_COMPLETE = '[psp] Save project complete',
  SAVE_PROJECT_FAILED = '[psp] Save project failed',
  CREATE_PROJECT = '[psp] Create project',
  CREATE_PROJECT_COMPLETE = '[psp] Create project complete',
  CREATE_PROJECT_FAILED = '[psp] Create project failed',
  GET_PROJECT_STATISTICS = '[psp] Get project statistics',
  GET_PROJECT_STATISTICS_COMPLETE = '[psp] Get project statistics complete',
  GET_PROJECT_STATISTICS_FAILED = '[psp] Get project statistics failed',
  GET_MORE_PROJECT_STATISTICS = '[psp] Get more project statistics',
  GET_SETTINGS = '[psp] Get settings',
  GET_SETTINGS_COMPLETE = '[psp] Get settings complete',
  GET_SETTINGS_FAILED = '[psp] Get settings failed',
  UPDATE_SETTINGS = '[psp] Update settings',
  UPDATE_SETTINGS_COMPLETE = '[psp] Update settings complete',
  UPDATE_SETTINGS_FAILED = '[psp] Update settings failed',
}

export class GetProjectsAction implements Action {
  readonly type = ParticipationActionTypes.GET_PROJECTS;
}

export class GetProjectsCompleteAction implements Action {
  readonly type = ParticipationActionTypes.GET_PROJECTS_COMPLETE;

  constructor(public payload: Project[]) {
  }
}

export class GetProjectsFailedAction implements Action {
  readonly type = ParticipationActionTypes.GET_PROJECTS_FAILED;

  constructor(public error: ApiError) {
  }
}

export class GetProjectAction implements Action {
  readonly type = ParticipationActionTypes.GET_PROJECT;

  constructor(public payload: { id: number }) {
  }
}

export class GetProjectCompleteAction implements Action {
  readonly type = ParticipationActionTypes.GET_PROJECT_COMPLETE;

  constructor(public payload: Project) {
  }
}

export class GetProjectFailedAction implements Action {
  readonly type = ParticipationActionTypes.GET_PROJECT_FAILED;

  constructor(public error: ApiError) {
  }
}

export class SaveProjectAction implements Action {
  readonly type = ParticipationActionTypes.SAVE_PROJECT;

  constructor(public payload: Project) {
  }
}

export class SaveProjectCompleteAction implements Action {
  readonly type = ParticipationActionTypes.SAVE_PROJECT_COMPLETE;

  constructor(public payload: Project) {
  }
}

export class SaveProjectFailedAction implements Action {
  readonly type = ParticipationActionTypes.SAVE_PROJECT_FAILED;

  constructor(public error: ApiError) {
  }
}

export class CreateProjectAction implements Action {
  readonly type = ParticipationActionTypes.CREATE_PROJECT;

  constructor(public payload: CreateProject) {
  }
}

export class CreateProjectCompleteAction implements Action {
  readonly type = ParticipationActionTypes.CREATE_PROJECT_COMPLETE;

  constructor(public payload: Project) {
  }
}

export class CreateProjectFailedAction implements Action {
  readonly type = ParticipationActionTypes.CREATE_PROJECT_FAILED;

  constructor(public error: ApiError) {
  }
}

export class GetProjectStatisticsAction implements Action {
  readonly type = ParticipationActionTypes.GET_PROJECT_STATISTICS;

  constructor(public payload: { id: number }) {
  }
}

export class GetProjectStatisticsCompleteAction implements Action {
  readonly type = ParticipationActionTypes.GET_PROJECT_STATISTICS_COMPLETE;

  constructor(public payload: ProjectStatistics) {
  }
}

export class GetMoreProjectStatisticsAction implements Action {
  readonly type = ParticipationActionTypes.GET_MORE_PROJECT_STATISTICS;

}

export class GetProjectStatisticsFailedAction implements Action {
  readonly type = ParticipationActionTypes.GET_PROJECT_STATISTICS_FAILED;

  constructor(public error: ApiError) {
  }
}

export class GetSettingsAction implements Action {
  readonly type = ParticipationActionTypes.GET_SETTINGS;

}

export class GetSettingsCompleteAction implements Action {
  readonly type = ParticipationActionTypes.GET_SETTINGS_COMPLETE;

  constructor(public payload: CitySettings) {
  }
}

export class GetSettingsFailedAction implements Action {
  readonly type = ParticipationActionTypes.GET_SETTINGS_FAILED;

  constructor(public error: ApiError) {
  }
}

export class UpdateSettingsAction implements Action {
  readonly type = ParticipationActionTypes.UPDATE_SETTINGS;

  constructor(public payload: CitySettings) {
  }
}

export class UpdateSettingsCompleteAction implements Action {
  readonly type = ParticipationActionTypes.UPDATE_SETTINGS_COMPLETE;

  constructor(public payload: CitySettings) {
  }
}

export class UpdateSettingsFailedAction implements Action {
  readonly type = ParticipationActionTypes.UPDATE_SETTINGS_FAILED;

  constructor(public error: ApiError) {
  }
}

export type ParticipationActions =
  GetProjectsAction
  | GetProjectsCompleteAction
  | GetProjectsFailedAction
  | GetProjectAction
  | GetProjectCompleteAction
  | GetProjectFailedAction
  | SaveProjectAction
  | SaveProjectCompleteAction
  | SaveProjectFailedAction
  | CreateProjectAction
  | CreateProjectCompleteAction
  | CreateProjectFailedAction
  | GetProjectStatisticsAction
  | GetProjectStatisticsCompleteAction
  | GetProjectStatisticsFailedAction
  | GetMoreProjectStatisticsAction
  | GetSettingsAction
  | GetSettingsCompleteAction
  | GetSettingsFailedAction
  | UpdateSettingsAction
  | UpdateSettingsCompleteAction
  | UpdateSettingsFailedAction;
