import { routerReducer } from '@ngrx/router-store';
import { ActionReducerMap, createSelector, MetaReducer } from '@ngrx/store';
import { environment } from '../environments/environment';
import { MergedRouteReducerState } from './shared/util/store-router';

export interface RootState {
  router: MergedRouteReducerState;
}

export const reducers: ActionReducerMap<RootState> = {
  router: routerReducer,
};


export const metaReducers: MetaReducer<RootState>[] = environment.production ? [] : [];

export const getRouterReducerState = (state: RootState) => state.router;
export const getMergedRoute = createSelector(getRouterReducerState, routerReducerState => routerReducerState?.state ?? {
  url: '',
  params: {},
  queryParams: {},
  data: {},
});

export const getRouteParams = createSelector(getMergedRoute, s => s.params);
