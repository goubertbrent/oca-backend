import { createFeatureSelector, createSelector } from '@ngrx/store';
import { mapsFeatureKey, MapsState } from './maps.reducer';

const featureSelector = createFeatureSelector<MapsState>(mapsFeatureKey);

export const getMapConfig = createSelector(featureSelector, s => s.mapConfig);
