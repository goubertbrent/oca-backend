import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType, EMPTY_ARRAY, initialStateResult, ResultState } from '../shared/util';
import { MapConfig } from './maps';
import {
  Incident,
  IncidentList,
  IncidentStatistics,
  IncidentStatisticsFilter,
  IncidentStatisticsList,
  IncidentStatsPerMonth,
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
  statistics: ResultState<RawIncidentStatistics[]>;
  statisticsFilter: IncidentStatisticsFilter | null;
}


export const initialState: ReportsState = {
  incidents: initialStateResult,
  incident: initialStateResult,
  mapConfig: initialStateResult,
  statisticsList: initialStateResult,
  statistics: initialStateResult,
  statisticsFilter: null,
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

export const getAllIncidentStatistics = createSelector(featureSelector, (s): IncidentStatsPerMonth[] => {
  if (s.statistics.result) {
    return s.statistics.result.map(monthStats => ({
      ...monthStats, data: monthStats.data.map(item => {
        const locationArray: [number, number] | [] = item[ 3 ];
        const converted: IncidentStatistics = {
          incidentId: item[ 0 ],
          statuses: item[ 1 ],
          tags: item[ 2 ],
          location: locationArray.length ? { lat: locationArray[ 0 ], lon: locationArray[ 1 ] } : null,
        };
        return converted;
      }),
    })).sort((first, second) => {
      if (first.year === second.year) {
        return first.month - second.month;
      }
      return first.year - second.year;
    });
  }
  return EMPTY_ARRAY;
});

export const getIncidentFilter = createSelector(featureSelector, s => s.statisticsFilter);
export const getFilteredIncidentsStats = createSelector(getAllIncidentStatistics, getIncidentFilter, (stats, filter) => {
  const resultMap = new Map<string, IncidentStatistics>();
  for (const statsPerMonth of stats) {
    if (!filter || filter.years.includes(statsPerMonth.year) && filter.months.includes(statsPerMonth.month)) {
      for (const incident of statsPerMonth.data) {
        const itemStats = resultMap.get(incident.incidentId);
        let mergedStats: IncidentStatistics;
        if (itemStats) {
          // Keep last location, categories, tags but merge the statuses
          mergedStats = { ...itemStats, statuses: [...new Set([...itemStats.statuses, ...incident.statuses])] };
        } else {
          mergedStats = incident;
        }
        resultMap.set(incident.incidentId, mergedStats);
      }
    }
  }
  return [...resultMap.values()];
});

export const getIncidentStatisticsTotals = createSelector(getFilteredIncidentsStats, stats => {
  const totals = {
    [ IncidentStatus.NEW ]: 0,
    [ IncidentStatus.IN_PROGRESS ]: 0,
    [ IncidentStatus.RESOLVED ]: 0,
  };
  for (const { statuses } of stats) {
    for (const status of statuses) {
      totals[ status ]++;
    }
  }
  return totals;
});

