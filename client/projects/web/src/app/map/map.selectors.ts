import {createFeatureSelector, createSelector} from '@ngrx/store';
import {mapFeatureKey, MapState} from './map.reducer';

export const selectNewsState = createFeatureSelector<MapState>(mapFeatureKey);

export const getSelectedMarker = createSelector(selectNewsState, state => state.selectedMarker)
