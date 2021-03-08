import {createReducer, on} from "@ngrx/store";
import {SelectedMarker} from './marker.model'
import {changeLayer, clickMarker} from "./map.actions";
import {environment} from "../../environments/environment";

export const mapFeatureKey = 'map';

export interface MapState {
  selectedMarker: SelectedMarker | null,
  selectedLayerId: string
}

export const initialMapState: MapState = {
  selectedMarker: null,
  selectedLayerId: environment.servicesCityLayerId,
};

export const mapReducer = createReducer(
  initialMapState,
  on(clickMarker, (state, action) =>
    ({...state, selectedMarker: action.selectedMarker})),
  on(changeLayer,(state, action) =>
    ({...state ,selectedLayerId : action.layerId}))
);

