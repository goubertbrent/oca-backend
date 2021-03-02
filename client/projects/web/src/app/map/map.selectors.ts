import {createFeatureSelector, createSelector} from '@ngrx/store';
import {mapFeatureKey, MapState} from './map.reducer';

export const selectMapState = createFeatureSelector<MapState>(mapFeatureKey);

export const getSelectedMarker = createSelector(selectMapState, state => state.selectedMarker)
export const getLayerId = createSelector(selectMapState, state => state.selectedLayerId)
export const getPreviousLayerId = createSelector(selectMapState, state => state.previousLayer)
