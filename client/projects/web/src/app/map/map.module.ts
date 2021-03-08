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
import {MatIconRegistry} from "@angular/material/icon";
import {SwiperModule} from "swiper/angular";
import {RouterModule, Routes} from "@angular/router";

const routes: Routes = [
  {path: '', component: MapComponent,}
]

@NgModule({
  declarations: [
    MapComponent,
    MapboxComponent,
    SidebarComponent,
    MarkerDetailComponent,
    LayerbarComponent,
  ],

  imports: [
    CommonModule,
    MaterialModule,
    StoreModule.forFeature(fromMap.mapFeatureKey, fromMap.mapReducer),
    RouterModule.forChild(routes),
    SwiperModule,
  ],
  exports: [MapComponent]
})
export class MapModule {

  constructor(private matIconRegistry: MatIconRegistry) {
    matIconRegistry.registerFontClassAlias('fontawesome', 'fa');
  }
}

