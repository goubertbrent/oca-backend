import {createAction, props} from '@ngrx/store';
import {SelectedMarker} from "./marker.model";

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
  props<{ selectedMarker: SelectedMarker }>()
);

export const changeLayer = createAction(
  '[Map] change layer on map',
  props<{layerId: string}>()
);
