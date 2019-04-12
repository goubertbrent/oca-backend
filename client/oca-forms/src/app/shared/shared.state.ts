import { createFeatureSelector, createSelector } from '@ngrx/store';
import { Budget } from './billing/billing';
import { DEFAULT_LIST_LOADABLE, DEFAULT_LOADABLE, Loadable } from './loadable/loadable';
import { AppStatistics, ServiceIdentityInfo, ServiceMenuDetail } from './rogerthat';


export const initialSharedState: SharedState = {
  serviceMenu: DEFAULT_LOADABLE,
  serviceInfo: DEFAULT_LOADABLE,
  appStatistics: DEFAULT_LIST_LOADABLE,
  budget: DEFAULT_LOADABLE,
};


export interface SharedState {
  serviceMenu: Loadable<ServiceMenuDetail>;
  serviceInfo: Loadable<ServiceIdentityInfo>;
  appStatistics: Loadable<AppStatistics[]>;
  budget: Loadable<Budget>;
}

const featureSelector = createFeatureSelector<SharedState>('shared');

export const getServiceMenu = createSelector(featureSelector, s => s.serviceMenu);
export const getInfo = createSelector(featureSelector, s => s.serviceInfo);
export const getAppStats = createSelector(featureSelector, s => s.appStatistics);
export const getBudget = createSelector(featureSelector, s => s.budget);
