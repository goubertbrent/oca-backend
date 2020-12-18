import { createAction, props } from '@ngrx/store';
import { MapConfig } from './maps';

export const GetMapConfigAction = createAction(
  '[reports] Get map config',
  props<{ appId: string }>(),
);

export const GetMapConfigCompleteAction = createAction(
  '[reports] Get map config success',
  props<{ payload: MapConfig }>(),
);

export const GetMapConfigFailedAction = createAction(
  '[reports] Get map config failed',
  props<{ error: string }>(),
);

export const SaveMapConfigAction = createAction(
  '[reports] Save map config',
  props<{ appId: string, payload: MapConfig }>(),
);

export const SaveMapConfigCompleteAction = createAction(
  '[reports] Save map config complete',
  props<{ payload: MapConfig }>(),
);

export const SaveMapConfigFailedAction = createAction(
  '[reports] Save map config failed',
  props<{ error: string }>(),
);
