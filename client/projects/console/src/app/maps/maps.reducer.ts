import { createReducer, on } from '@ngrx/store';
import { initialStateResult, ResultState, stateError, stateLoading, stateSuccess } from '@oca/web-shared';
import { MapConfig } from './maps';
import {
  GetMapConfigAction,
  GetMapConfigCompleteAction,
  GetMapConfigFailedAction,
  SaveMapConfigAction,
  SaveMapConfigCompleteAction,
  SaveMapConfigFailedAction,
} from './maps.actions';


export const mapsFeatureKey = 'maps';

export interface MapsState {
  mapConfig: ResultState<MapConfig>;
}

export const initialState: MapsState = {
  mapConfig: initialStateResult,
};

export const mapsReducer = createReducer(
  initialState,
  on(GetMapConfigAction, (state) => ({ ...state, mapConfig: stateLoading(initialState.mapConfig.result) })),
  on(GetMapConfigCompleteAction, (state, { payload }) => ({ ...state, mapConfig: stateSuccess(payload) })),
  on(GetMapConfigFailedAction, (state, { error }) => ({ ...state, mapConfig: stateError(error, state.mapConfig.result) })),
  on(SaveMapConfigAction, (state, { payload }) => ({ ...state, mapConfig: stateLoading(payload) })),
  on(SaveMapConfigCompleteAction, (state, { payload }) => ({ ...state, mapConfig: stateSuccess(payload) })),
  on(SaveMapConfigFailedAction, (state, { error }) => ({ ...state, mapConfig: stateError(error, state.mapConfig.result) })),
);
