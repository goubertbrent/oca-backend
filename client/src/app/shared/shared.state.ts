import { createFeatureSelector, createSelector } from '@ngrx/store';
import { Budget } from './billing/billing';
import { BrandingSettings, SolutionSettings } from './interfaces/oca';
import { App, AppStatistics, AppStatisticsMapping, ServiceIdentityInfo, ServiceMenuDetail } from './interfaces/rogerthat';
import { DEFAULT_LIST_LOADABLE, DEFAULT_LOADABLE, Loadable } from './loadable/loadable';


export const initialSharedState: SharedState = {
  serviceMenu: DEFAULT_LOADABLE,
  serviceIdentityInfo: DEFAULT_LOADABLE,
  apps: DEFAULT_LIST_LOADABLE,
  appStatistics: DEFAULT_LIST_LOADABLE,
  budget: DEFAULT_LOADABLE,
  solutionSettings: DEFAULT_LOADABLE,
  brandingSettings: DEFAULT_LOADABLE,
};


export interface SharedState {
  serviceMenu: Loadable<ServiceMenuDetail>;
  serviceIdentityInfo: Loadable<ServiceIdentityInfo>;
  apps: Loadable<App[]>;
  appStatistics: Loadable<AppStatistics[]>;
  budget: Loadable<Budget>;
  solutionSettings: Loadable<SolutionSettings>;
  brandingSettings: Loadable<BrandingSettings>;
}

const featureSelector = createFeatureSelector<SharedState>('shared');

export const getServiceMenu = createSelector(featureSelector, s => s.serviceMenu);
export const getServiceIdentityInfo = createSelector(featureSelector, s => s.serviceIdentityInfo);
export const getApps = createSelector(featureSelector, s => s.apps);
export const getBudget = createSelector(featureSelector, s => s.budget);
export const getAppStatistics = createSelector(featureSelector, s => {
  const mapping: AppStatisticsMapping = {};
  if (s.appStatistics.data) {
    for (const app of s.appStatistics.data) {
      mapping[ app.app_id ] = app;
    }
  }
  return mapping;
});
export const getSolutionSettings = createSelector(featureSelector, s => s.solutionSettings);
export const getBrandingSettings = createSelector(featureSelector, s => s.brandingSettings);
