import { Action } from '@ngrx/store';
import { ErrorAction } from '@oca/web-shared';
import { MapConfig } from './maps';
import { Incident, IncidentList, IncidentStatus } from './pages/reports';

export const enum ReportsActionTypes {
  GET_INCIDENTS = '[reports] Get incidents',
  GET_INCIDENTS_COMPLETE = '[reports] Get incidents complete',
  GET_INCIDENTS_FAILED = '[reports] Get incidents failed',
  GET_INCIDENT = '[reports] Get incident',
  GET_INCIDENT_COMPLETE = '[reports] Get incident complete',
  GET_INCIDENT_FAILED = '[reports] Get incident failed',
  UPDATE_INCIDENT = '[reports] Update incident',
  UPDATE_INCIDENT_COMPLETE = '[reports] Update incident complete',
  UPDATE_INCIDENT_FAILED = '[reports] Update incident failed',
  GET_MAP_CONFIG = '[reports] Get map config',
  GET_MAP_CONFIG_COMPLETE = '[reports] Get map config complete',
  GET_MAP_CONFIG_FAILED = '[reports] Get map config failed',
  SAVE_MAP_CONFIG = '[reports] Save map config',
  SAVE_MAP_CONFIG_COMPLETE = '[reports] Save map config complete',
  SAVE_MAP_CONFIG_FAILED = '[reports] Save map config failed',
}

export class GetIncidentsAction implements Action {
  readonly type = ReportsActionTypes.GET_INCIDENTS;

  constructor(public payload: { status: IncidentStatus, cursor: string | null }) {
  }
}

export class GetIncidentsCompleteAction implements Action {
  readonly type = ReportsActionTypes.GET_INCIDENTS_COMPLETE;

  constructor(public payload: IncidentList) {
  }
}

export class GetIncidentsFailedAction implements ErrorAction {
  readonly type = ReportsActionTypes.GET_INCIDENTS_FAILED;

  constructor(public error: string) {
  }
}

export class GetIncidentAction implements Action {
  readonly type = ReportsActionTypes.GET_INCIDENT;

  constructor(public payload: { id: string }) {
  }
}

export class GetIncidentCompleteAction implements Action {
  readonly type = ReportsActionTypes.GET_INCIDENT_COMPLETE;

  constructor(public payload: Incident) {
  }
}

export class GetIncidentFailedAction implements ErrorAction {
  readonly type = ReportsActionTypes.GET_INCIDENT_FAILED;

  constructor(public error: string) {
  }
}

export class UpdateIncidentAction implements Action {
  readonly type = ReportsActionTypes.UPDATE_INCIDENT;

  constructor(public payload: Incident) {
  }
}

export class UpdateIncidentCompleteAction implements Action {
  readonly type = ReportsActionTypes.UPDATE_INCIDENT_COMPLETE;

  constructor(public payload: Incident) {
  }
}

export class UpdateIncidentFailedAction implements ErrorAction {
  readonly type = ReportsActionTypes.UPDATE_INCIDENT_FAILED;

  constructor(public error: string) {
  }
}

export class GetMapConfigAction implements Action {
  readonly type = ReportsActionTypes.GET_MAP_CONFIG;
}

export class GetMapConfigCompleteAction implements Action {
  readonly type = ReportsActionTypes.GET_MAP_CONFIG_COMPLETE;

  constructor(public payload: MapConfig) {
  }
}

export class GetMapConfigFailedAction implements ErrorAction {
  readonly type = ReportsActionTypes.GET_MAP_CONFIG_FAILED;

  constructor(public error: string) {
  }
}

export class SaveMapConfigAction implements Action {
  readonly type = ReportsActionTypes.SAVE_MAP_CONFIG;

  constructor(public payload: MapConfig) {
  }
}

export class SaveMapConfigCompleteAction implements Action {
  readonly type = ReportsActionTypes.SAVE_MAP_CONFIG_COMPLETE;

  constructor(public payload: MapConfig) {
  }
}

export class SaveMapConfigFailedAction implements ErrorAction {
  readonly type = ReportsActionTypes.SAVE_MAP_CONFIG_FAILED;

  constructor(public error: string) {
  }
}

export type ReportsActions = GetIncidentsAction
  | GetIncidentsCompleteAction
  | GetIncidentsFailedAction
  | GetMapConfigAction
  | GetMapConfigCompleteAction
  | GetMapConfigFailedAction
  | SaveMapConfigAction
  | SaveMapConfigCompleteAction
  | SaveMapConfigFailedAction
  | GetIncidentAction
  | GetIncidentCompleteAction
  | GetIncidentFailedAction
  | UpdateIncidentAction
  | UpdateIncidentCompleteAction
  | UpdateIncidentFailedAction;
