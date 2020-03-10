import { createFeatureSelector, createSelector } from '@ngrx/store';
import { AvailablePlaceType, OpeningHours } from '../shared/interfaces/oca';
import { CallStateType, initialStateResult, ResultState } from '../shared/util';
import { ServiceInfo } from './service-info/service-info';


export const initialSettingsState: SettingsState = {
  openingHours: initialStateResult,
  serviceInfo: initialStateResult,
  availablePlaceTypes: initialStateResult,
};


export interface SettingsState {
  openingHours: ResultState<OpeningHours>;
  serviceInfo: ResultState<ServiceInfo>;
  availablePlaceTypes: ResultState<AvailablePlaceType[]>;
}

const featureSelector = createFeatureSelector<SettingsState>('settings');

export const getOpeningHours = createSelector(featureSelector, s => s.openingHours.result);
export const openingHoursLoading = createSelector(featureSelector, s => s.openingHours.state === CallStateType.LOADING);

export const getServiceInfo = createSelector(featureSelector, s => s.serviceInfo.result);
export const isServiceInfoLoading = createSelector(featureSelector, s => s.serviceInfo.state === CallStateType.LOADING);
export const getAvailablePlaceTypes = createSelector(featureSelector, s => s.availablePlaceTypes.result ?? []);
export const isPlaceTypesLoading = createSelector(featureSelector, s => s.availablePlaceTypes.state === CallStateType.LOADING);
