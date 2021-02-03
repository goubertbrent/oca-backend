import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType } from '@oca/web-shared';
import { pointOfInterestFeatureKey, State } from './point-of-interest.reducer';

export const selectPoiState = createFeatureSelector<State>(pointOfInterestFeatureKey);

export const getPointOfInterests = createSelector(selectPoiState, s => s.poiList.result?.results ?? []);
export const getPOICursor = createSelector(selectPoiState, s => s.poiList.result?.cursor);
export const isLoadingPoiList = createSelector(selectPoiState, s => s.poiList.state === CallStateType.LOADING);
export const getPoiFilter = createSelector(selectPoiState, s => s.poiFilter);
export const hasMorePoi = createSelector(selectPoiState, s => s.poiList.result?.more ?? false);
export const getCurrentPointOfInterest = createSelector(selectPoiState, s => s.currentPOI.result);
export const isLoadingPoi = createSelector(selectPoiState, s => s.currentPOI.state === CallStateType.LOADING);
