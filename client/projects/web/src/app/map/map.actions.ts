import { createAction, props } from '@ngrx/store';
import {Marker} from "./marker.model";

export const loadMaps = createAction(
  '[Map] Load Maps'
);

export const loadMapsSuccess = createAction(
  '[Map] Load Maps Success',
  props<{ data: any }>()
);

export const loadMapsFailure = createAction(
  '[Map] Load Maps Failure',
  props<{ error: any }>()
);

export const clickMarker = createAction(
  '[Map] save selected feature',
  props<{selectedMarker : Marker}>()
);
