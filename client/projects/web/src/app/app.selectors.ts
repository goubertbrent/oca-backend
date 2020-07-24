import { createFeatureSelector, createSelector } from '@ngrx/store';
import { appRootSelector, AppState } from './app.reducer';

const featureSelector = createFeatureSelector<AppState>(appRootSelector);

export const getAppInfo = createSelector(featureSelector, s => s.appInfo.result);
