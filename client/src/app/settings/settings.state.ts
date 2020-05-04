import { createFeatureSelector, createSelector } from '@ngrx/store';
import { AvailablePlaceType, OpeningHours, PlaceType } from '../shared/interfaces/oca';
import { CallStateType, initialStateResult, ResultState } from '../shared/util';
import { Country, ServiceInfo } from './service-info/service-info';


export const initialSettingsState: SettingsState = {
  openingHours: initialStateResult,
  serviceInfo: initialStateResult,
  availablePlaceTypes: initialStateResult,
  countries: initialStateResult,
};


export interface SettingsState {
  openingHours: ResultState<OpeningHours>;
  serviceInfo: ResultState<ServiceInfo>;
  availablePlaceTypes: ResultState<PlaceType[]>;
  countries: ResultState<Country[]>;
}

const featureSelector = createFeatureSelector<SettingsState>('settings');

export const getOpeningHours = createSelector(featureSelector, s => s.openingHours.result);
export const openingHoursLoading = createSelector(featureSelector, s => s.openingHours.state === CallStateType.LOADING);

export const getServiceInfo = createSelector(featureSelector, s => s.serviceInfo.result);
export const isServiceInfoLoading = createSelector(featureSelector, s => s.serviceInfo.state === CallStateType.LOADING);
export const getAvailablePlaceTypes = createSelector(featureSelector, (s): AvailablePlaceType[] => {
  return s.availablePlaceTypes.result?.map(([value, label]) => ({ value, label })) ?? [];
});
export const isPlaceTypesLoading = createSelector(featureSelector, s => s.availablePlaceTypes.state === CallStateType.LOADING);
export const areCountriesLoading = createSelector(featureSelector, s => s.countries.state === CallStateType.LOADING);
export const getCountries = createSelector(featureSelector, s => s.countries.result ?? []);
