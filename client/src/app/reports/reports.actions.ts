import { Action } from '@ngrx/store';
import { ErrorAction } from '@oca/web-shared';
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

export type ReportsActions = GetIncidentsAction
  | GetIncidentsCompleteAction
  | GetIncidentsFailedAction
  | GetIncidentAction
  | GetIncidentCompleteAction
  | GetIncidentFailedAction
  | UpdateIncidentAction
  | UpdateIncidentCompleteAction
  | UpdateIncidentFailedAction;
