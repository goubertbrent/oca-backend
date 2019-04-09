import { createFeatureSelector, createSelector } from '@ngrx/store';
import { DEFAULT_LOADABLE, Loadable } from './loadable/loadable';
import { ServiceMenuDetail } from './rogerthat';


export const initialSharedState: SharedState = {
  serviceMenu: DEFAULT_LOADABLE,
};


export interface SharedState {
  serviceMenu: Loadable<ServiceMenuDetail>;
}

const featureSelector = createFeatureSelector<SharedState>('shared');

export const getServiceMenu = createSelector(featureSelector, s => s.serviceMenu);
