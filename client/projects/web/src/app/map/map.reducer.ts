import {createReducer, on} from "@ngrx/store";
import {Marker} from './marker.model'
import {clickMarker} from "./map.actions";

export const mapFeatureKey = 'map';

export interface MapState {
  selectedMarker: Marker | null
}

export const initialMapState: MapState = {
  selectedMarker: null
};

export const mapReducer = createReducer(
  initialMapState,
  on(clickMarker, (state, action) => ({...state, selectedMarker: action.selectedMarker}))
);

