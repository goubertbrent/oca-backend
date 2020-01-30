import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType, EMPTY_ARRAY, initialStateResult, ResultState } from '../shared/util';
import { MapConfig } from './maps';
import {
  Incident,
  IncidentList,
  IncidentStatistics,
  IncidentStatisticsList,
  IncidentStatus,
  IncidentTagType,
  RawIncidentStatistics,
  TagFilter,
  TagFilterMapping,
} from './reports';


export interface ReportsState {
  incidents: ResultState<IncidentList>;
  incident: ResultState<Incident>;
  mapConfig: ResultState<MapConfig>;
  statisticsList: ResultState<IncidentStatisticsList>;
  statistics: ResultState<RawIncidentStatistics>;
}


export const initialState: ReportsState = {
  incidents: initialStateResult,
  incident: initialStateResult,
  mapConfig: initialStateResult,
  statisticsList: initialStateResult,
  statistics: initialStateResult,
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
export const statisticsLoading = createSelector(featureSelector, s => s.statisticsList.state === CallStateType.LOADING ||
  s.statistics.state === CallStateType.LOADING);
export const getStatisticsList = createSelector(featureSelector, s => s.statisticsList.result || {
  categories: EMPTY_ARRAY,
  subcategories: EMPTY_ARRAY,
  results: EMPTY_ARRAY,
});

export const getStatisticsMonths = createSelector(getStatisticsList, s => s.results
  .reduce((acc, result): { [ key: number ]: number[] } => {
    acc[ result.year ] = result.months;
    return acc;
  }, {}),
);

export const getTagList = createSelector(getStatisticsList, list => {
  const tagList: TagFilter[] = [];
  for (const cat of list.categories) {
    tagList.push({ id: `${IncidentTagType.CATEGORY}#${cat.id}`, type: IncidentTagType.CATEGORY, name: cat.name });
  }
  for (const cat of list.subcategories) {
    tagList.push({ id: `${IncidentTagType.SUBCATEGORY}#${cat.id}`, type: IncidentTagType.SUBCATEGORY, name: cat.name });
  }
  return tagList;
});
export const getTagNameMapping = createSelector(getTagList, list => {
  const tagNames: TagFilterMapping = {};
  for (const cat of list) {
    tagNames[ cat.id ] = cat;
  }
  return tagNames;
});
export const getIncidentStatistics = createSelector(featureSelector, (s): IncidentStatistics[] => {
  if (s.statistics.result) {
    return s.statistics.result.statistics.map(item => {
      const locationArray: [number, number] | [] = item[ 3 ];
      return {
        incidentId: item[ 0 ],
        statuses: item[ 1 ],
        tags: item[ 2 ],
        location: locationArray.length ? { lat: locationArray[ 0 ], lon: locationArray[ 1 ] } : null,
      } as IncidentStatistics;
    });
  }
  return EMPTY_ARRAY;
});
export const getIncidentStatisticsTotals = createSelector(getIncidentStatistics, incidents => {
  const totals = {
    [ IncidentStatus.NEW ]: 0,
    [ IncidentStatus.IN_PROGRESS ]: 0,
    [ IncidentStatus.RESOLVED ]: 0,
  };
  for (const incident of incidents) {
    for (const status of incident.statuses) {
      totals[ status ]++;
    }
  }
  return totals;
});



