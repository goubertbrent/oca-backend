import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType, initialStateResult, ResultState } from '@oca/web-shared';
import { Budget } from './billing/billing';
import { BrandingSettings, GlobalConfig, SolutionSettings } from './interfaces/oca';
import { DEFAULT_LOADABLE, Loadable } from './loadable/loadable';


export const initialSharedState: SharedState = {
  budget: DEFAULT_LOADABLE,
  solutionSettings: DEFAULT_LOADABLE,
  brandingSettings: initialStateResult,
  globalConfig: initialStateResult,
};


export interface SharedState {
  budget: Loadable<Budget>;
  solutionSettings: Loadable<SolutionSettings>;
  brandingSettings: ResultState<BrandingSettings>;
  globalConfig: ResultState<GlobalConfig>;
}

const featureSelector = createFeatureSelector<SharedState>('shared');

export const getBudget = createSelector(featureSelector, s => s.budget);
export const getSolutionSettings = createSelector(featureSelector, s => s.solutionSettings);
export const getBrandingSettings = createSelector(featureSelector, s => s.brandingSettings.result);
export const isBrandingSettingsLoading = createSelector(featureSelector, s => s.brandingSettings.state === CallStateType.LOADING);
export const getGlobalConfig = createSelector(featureSelector, s => s.globalConfig);
export const isShopUser = createSelector(getGlobalConfig, s => s.result ? s.result.is_shop_user : false);
