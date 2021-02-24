import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType } from '@oca/web-shared';
import { mapFeatureKey, MapState } from './map.reducer';
import {Marker} from "./marker.model";

export const selectNewsState = createFeatureSelector<MapState>(mapFeatureKey);

export const getSelectedMarker = createSelector(selectNewsState, state => state.selectedMarker)
