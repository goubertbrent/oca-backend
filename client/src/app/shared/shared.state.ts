import { createFeatureSelector, createSelector } from '@ngrx/store';
import { App, AppStatistics, AppStatisticsMapping, CallStateType, initialStateResult, ResultState } from '@oca/web-shared';
import { Budget } from './billing/billing';
import { BrandingSettings, GlobalConfig, SolutionSettings } from './interfaces/oca';
import { ServiceIdentityInfo } from './interfaces/rogerthat';
import { DEFAULT_LIST_LOADABLE, DEFAULT_LOADABLE, Loadable } from './loadable/loadable';


export const initialSharedState: SharedState = {
  serviceIdentityInfo: DEFAULT_LOADABLE,
  apps: DEFAULT_LIST_LOADABLE,
  appStatistics: DEFAULT_LIST_LOADABLE,
  budget: DEFAULT_LOADABLE,
  solutionSettings: DEFAULT_LOADABLE,
  brandingSettings: initialStateResult,
  globalConfig: initialStateResult,
};


export interface SharedState {
  serviceIdentityInfo: Loadable<ServiceIdentityInfo>;
  apps: Loadable<App[]>;
  appStatistics: Loadable<AppStatistics[]>;
  budget: Loadable<Budget>;
  solutionSettings: Loadable<SolutionSettings>;
  brandingSettings: ResultState<BrandingSettings>;
  globalConfig: ResultState<GlobalConfig>;
}

const featureSelector = createFeatureSelector<SharedState>('shared');

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
export const getBrandingSettings = createSelector(featureSelector, s => s.brandingSettings.result);
export const isBrandingSettingsLoading = createSelector(featureSelector, s => s.brandingSettings.state === CallStateType.LOADING);
export const getGlobalConfig = createSelector(featureSelector, s => s.globalConfig);
export const isShopUser = createSelector(getGlobalConfig, s => s.result ? s.result.is_shop_user : false);
