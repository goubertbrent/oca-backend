import {createReducer, on} from "@ngrx/store";
import {SelectedMarker} from './marker.model'
import {clickMarker} from "./map.actions";

export const mapFeatureKey = 'map';

export interface MapState {
  selectedMarker: SelectedMarker | null
}

export const initialMapState: MapState = {
  selectedMarker: null
};

export const mapReducer = createReducer(
  initialMapState,
  on(clickMarker, (state, action) =>
    ({...state, selectedMarker: action.selectedMarker}))
);

