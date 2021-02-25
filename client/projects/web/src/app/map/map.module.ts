import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {StoreModule} from '@ngrx/store';
import * as fromMap from './map.reducer';
import {MapComponent} from "./map.component";
import {MapboxComponent} from "./mapbox/mapbox.component";
import {SidebarComponent} from "./sidebar/sidebar.component";
import {MarkerDetailComponent} from "./sidebar/marker-detail/marker-detail.component";
import {LayerbarComponent} from './mapbox/layerbar/layerbar.component';
import {MaterialModule} from "../material/material.module";


@NgModule({
  declarations: [
    MapComponent,
    MapboxComponent,
    SidebarComponent,
    MarkerDetailComponent,
    LayerbarComponent
  ],

  imports: [
    CommonModule,
    MaterialModule,
    StoreModule.forFeature(fromMap.mapFeatureKey, fromMap.mapReducer)
  ],
  exports: [MapComponent]
})
export class MapModule {
}
