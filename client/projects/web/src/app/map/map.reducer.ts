import {createReducer, on} from "@ngrx/store";
import {SelectedMarker} from './marker.model'
import {changeLayer, clickMarker} from "./map.actions";
import {environment} from "../../environments/environment";
import {state} from "@angular/animations";

export const mapFeatureKey = 'map';

export interface MapState {
  selectedMarker: SelectedMarker | null,
  selectedLayerId: string
  previousLayer: string
}

export const initialMapState: MapState = {
  selectedMarker: null,
  selectedLayerId: environment.servicesCityLayerId,
  previousLayer: "",
};

export const mapReducer = createReducer(
  initialMapState,
  on(clickMarker, (state, action) =>
    ({...state, selectedMarker: action.selectedMarker})),
  on(changeLayer,(state, action) =>
    ({...state, previousLayer: state.selectedLayerId ,selectedLayerId : action.layerId}))
);

