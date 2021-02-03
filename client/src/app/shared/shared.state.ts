import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType, initialStateResult, ResultState } from '@oca/web-shared';
import { Budget } from './billing/billing';
import { AvailablePlaceType, BrandingSettings, Country, GlobalConfig, PlaceType, SolutionSettings } from './interfaces/oca';
import { DEFAULT_LOADABLE, Loadable } from './loadable/loadable';


export const initialSharedState: SharedState = {
  budget: DEFAULT_LOADABLE,
  solutionSettings: DEFAULT_LOADABLE,
  brandingSettings: initialStateResult,
  globalConfig: initialStateResult,
  countries: initialStateResult,
  availablePlaceTypes: initialStateResult,
};


export interface SharedState {
  budget: Loadable<Budget>;
  solutionSettings: Loadable<SolutionSettings>;
  brandingSettings: ResultState<BrandingSettings>;
  globalConfig: ResultState<GlobalConfig>;
  countries: ResultState<Country[]>;
  availablePlaceTypes: ResultState<PlaceType[]>;
}

const featureSelector = createFeatureSelector<SharedState>('shared');

export const getBudget = createSelector(featureSelector, s => s.budget);
export const getSolutionSettings = createSelector(featureSelector, s => s.solutionSettings);
export const getBrandingSettings = createSelector(featureSelector, s => s.brandingSettings.result);
export const isBrandingSettingsLoading = createSelector(featureSelector, s => s.brandingSettings.state === CallStateType.LOADING);
export const getGlobalConfig = createSelector(featureSelector, s => s.globalConfig);
export const isShopUser = createSelector(getGlobalConfig, s => s.result ? s.result.is_shop_user : false);
export const countriesLoading = createSelector(featureSelector, s => s.countries.state === CallStateType.LOADING);
export const getCountries = createSelector(featureSelector, s => s.countries.result ?? []);
export const getAvailablePlaceTypesState = createSelector(featureSelector, s => s.availablePlaceTypes);
export const getAvailablePlaceTypes = createSelector(featureSelector, (s): AvailablePlaceType[] => {
  return s.availablePlaceTypes.result?.map(([value, label]) => ({ value, label })) ?? [];
});
export const isPlaceTypesLoading = createSelector(featureSelector, s => s.availablePlaceTypes.state === CallStateType.LOADING);

