import { createFeatureSelector, createSelector } from '@ngrx/store';
import { IToolbarState } from './states';

export const selectToolbarState = createFeatureSelector<IToolbarState>('toolbar');
export const getToolbarItems = createSelector(selectToolbarState, s => s.items);
