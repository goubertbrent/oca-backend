import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType, initialStateResult, ResultState } from '@oca/web-shared';
import { ServiceOpeningHours } from '../shared/interfaces/oca';
import { ServiceInfo } from './service-info/service-info';


export const initialSettingsState: SettingsState = {
  openingHours: initialStateResult,
  serviceInfo: initialStateResult,
};


export interface SettingsState {
  openingHours: ResultState<ServiceOpeningHours>;
  serviceInfo: ResultState<ServiceInfo>;
}

const featureSelector = createFeatureSelector<SettingsState>('settings');

export const getOpeningHours = createSelector(featureSelector, s => s.openingHours.result);
export const openingHoursLoading = createSelector(featureSelector, s => s.openingHours.state === CallStateType.LOADING);

export const getServiceInfo = createSelector(featureSelector, s => s.serviceInfo.result);
export const isServiceInfoLoading = createSelector(featureSelector, s => s.serviceInfo.state === CallStateType.LOADING);
