import { createFeatureSelector, createSelector } from '@ngrx/store';
import { Route } from '../../../../src/app/app.routes';
import { SidebarItem } from './sidebar.interfaces';

export interface ISidebarState {
  routes: Route[];
  sidebarItems: SidebarItem[];
}

export const initialSidebarState: ISidebarState = {
  routes: [],
  sidebarItems: [],
};

export const selectSidebarState = createFeatureSelector<ISidebarState>('sidebar');
export const getRoutes = createSelector(selectSidebarState, s => s.routes);
export const getSidebarItems = createSelector(selectSidebarState, s => s.sidebarItems);
