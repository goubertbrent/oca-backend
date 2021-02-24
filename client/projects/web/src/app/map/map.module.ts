import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StoreModule } from '@ngrx/store';
import * as fromMap from './map.reducer';
import {MapComponent} from "./map.component";
import {MapboxComponent} from "./mapbox/mapbox.component";
import {SidebarComponent} from "./sidebar/sidebar.component";
import {MarkerDetailComponent} from "./sidebar/marker-detail/marker-detail.component";
import {MatCardModule} from "@angular/material/card";
import {MatButtonModule} from "@angular/material/button";
import {MatIconModule} from "@angular/material/icon";



@NgModule({
  declarations: [
    MapComponent,
    MapboxComponent,
    SidebarComponent,
    MarkerDetailComponent
  ],

  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    StoreModule.forFeature(fromMap.mapFeatureKey, fromMap.mapReducer)
  ],
  exports: [MapComponent]
})
export class MapModule { }
