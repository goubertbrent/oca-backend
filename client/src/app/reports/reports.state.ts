import { createFeatureSelector, createSelector } from '@ngrx/store';
import { initialStateResult, ResultState } from '../shared/util';
import { MapConfig } from './maps';
import { Incident, IncidentList } from './pages/reports';


export interface ReportsState {
  incidents: IncidentList;
  incident: ResultState<Incident>;
  mapConfig: ResultState<MapConfig>;
}


export const initialState: ReportsState = {
  incidents: { cursor: null, more: true, results: [] },
  incident: initialStateResult,
  mapConfig: initialStateResult,
};

const featureSelector = createFeatureSelector<ReportsState>('reports');

export const getIncidents = createSelector(featureSelector, s => s.incidents);
export const getIncident = createSelector(featureSelector, s => s.incident);
export const getMapConfig = createSelector(featureSelector, s => s.mapConfig);


