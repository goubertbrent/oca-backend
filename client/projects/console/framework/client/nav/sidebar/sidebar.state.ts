import { createFeatureSelector, createSelector } from '@ngrx/store';
import { ISidebarState } from './states';

export const selectSidebarState = createFeatureSelector<ISidebarState>('sidebar');
export const getRoutes = createSelector(selectSidebarState, s => s.routes);
export const getSidebarItems = createSelector(selectSidebarState, s => s.sidebarItems);
