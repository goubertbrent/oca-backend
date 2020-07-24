import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType, initialStateResult, ResultState } from '@oca/web-shared';
import { MapConfig } from './maps';
import { Incident, IncidentList } from './pages/reports';


export interface ReportsState {
  incidents: ResultState<IncidentList>;
  incident: ResultState<Incident>;
  mapConfig: ResultState<MapConfig>;
}


export const initialState: ReportsState = {
  incidents: initialStateResult,
  incident: initialStateResult,
  mapConfig: initialStateResult,
};

const featureSelector = createFeatureSelector<ReportsState>('reports');

export const getIncidents = createSelector(featureSelector, s => s.incidents.result ? s.incidents.result : {
  cursor: null,
  results: [],
  more: false,
} as IncidentList);
export const incidentsLoading = createSelector(featureSelector, s => s.incidents.state === CallStateType.LOADING);
export const getIncident = createSelector(featureSelector, s => s.incident);
export const getMapConfig = createSelector(featureSelector, s => s.mapConfig);


